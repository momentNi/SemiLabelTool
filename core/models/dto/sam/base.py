import os

import cv2
import numpy as np
from PyQt5.QtCore import QPointF

from core.configs.constants import Constants
from core.dto.enums import ShapeType, AutoLabelEditMode
from core.dto.shape import Shape
from core.models.dto.base import Model, AutoLabelingResult, ModelInfo
from core.models.dto.clip import ChineseClipONNX
from core.models.dto.sam.sam_onnx import SegmentAnythingONNX
from core.services.system import show_critical_message
from utils.image import qt_img_to_rgb_cv_img
from utils.lru_cache import LRUCache


class SegmentAnything(Model):

    def __init__(self, model_info: ModelInfo):
        super().__init__(model_info)

        self.input_size = self.configs["input_size"]
        self.max_width = self.configs["max_width"]
        self.max_height = self.configs["max_height"]

        # Get encoder and decoder model paths
        encoder_model_abs_path = self.fetch_model("encoder_model_path")
        if not encoder_model_abs_path or not os.path.isfile(encoder_model_abs_path):
            show_critical_message("Error", f"Could not download or initialize {self.model_info.model_type} model. No encoder model.")

        decoder_model_abs_path = self.fetch_model("decoder_model_path")
        if not decoder_model_abs_path or not os.path.isfile(decoder_model_abs_path):
            show_critical_message("Error", f"Could not download or initialize {self.model_info.model_type} model. No decoder model.")

        # Load models
        self.model = SegmentAnythingONNX(encoder_model_abs_path, decoder_model_abs_path)

        # Mark for auto labeling: points, rectangles
        self.marks = []

        # Cache for image embedding
        self.cache_size = 10
        self.preloaded_size = self.cache_size - 3
        self.image_embedding_cache = LRUCache(self.cache_size)

        # Pre-inference worker
        self.pre_inference_thread = None
        self.pre_inference_worker = None
        self.stop_inference = False

        # CLIP models
        self.clip_net = None
        clip_txt_model_path = self.configs.get("txt_model_path", "")
        clip_img_model_path = self.configs.get("img_model_path", "")
        if clip_txt_model_path and clip_img_model_path:
            if self.configs["model_type"] == "cn_clip":
                model_arch = self.configs["model_arch"]
                self.clip_net = ChineseClipONNX(
                    clip_txt_model_path,
                    clip_img_model_path,
                    model_arch,
                    device=Constants.DEVICE,
                )
            self.classes = self.configs.get("classes", [])

    def unload(self):
        self.stop_inference = True
        if self.pre_inference_thread:
            self.pre_inference_thread.quit()

    def predict_shapes(self, image, image_path=None, **kwargs) -> AutoLabelingResult:
        if image is None or not self.marks:
            return AutoLabelingResult(self.model_info.name, [], replace=False)

        cv_image = qt_img_to_rgb_cv_img(image, image_path)
        # noinspection PyBroadException
        try:
            # Use cached image embedding if possible
            cached_data = self.image_embedding_cache.get(image_path)
            if cached_data is not None:
                image_embedding = cached_data
            else:
                if self.stop_inference:
                    return AutoLabelingResult(self.model_info.name, [], replace=False)
                image_embedding = self.model.encode(cv_image)
                self.image_embedding_cache.put(
                    image_path,
                    image_embedding,
                )
            if self.stop_inference:
                return AutoLabelingResult(self.model_info.name, [], replace=False)
            masks = self.model.predict_masks(image_embedding, self.marks)
            if len(masks.shape) == 4:
                masks = masks[0][0]
            else:
                masks = masks[0]
            shapes = self.post_process(masks, cv_image)
        except Exception as e:
            show_critical_message("Error", f"Could not inference model: {e}", trace=True)
            return AutoLabelingResult(self.model_info.name, [], replace=False)

        result = AutoLabelingResult(self.model_info.name, shapes, replace=False)
        return result

    def post_process(self, masks, image=None):
        """
        Post process masks
        """
        # Find contours
        masks[masks > 0.0] = 255
        masks[masks <= 0.0] = 0
        masks = masks.astype(np.uint8)
        contours, _ = cv2.findContours(masks, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

        # Refine contours
        approx_contours = []
        for contour in contours:
            # Approximate contour
            epsilon = 0.001 * cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon, True)
            approx_contours.append(approx)

        # Remove too big contours ( >90% of image size)
        if len(approx_contours) > 1:
            image_size = masks.shape[0] * masks.shape[1]
            areas = [cv2.contourArea(contour) for contour in approx_contours]
            filtered_approx_contours = [
                contour
                for contour, area in zip(approx_contours, areas)
                if area < image_size * 0.9
            ]
            approx_contours = filtered_approx_contours

        # Remove small contours (area < 20% of average area)
        if len(approx_contours) > 1:
            areas = [cv2.contourArea(contour) for contour in approx_contours]
            avg_area = np.mean(areas)

            filtered_approx_contours = [
                contour
                for contour, area in zip(approx_contours, areas)
                if area > avg_area * 0.2
            ]
            approx_contours = filtered_approx_contours

        # Contours to shapes
        shapes = []
        if self.output_mode == ShapeType.POLYGON:
            for approx in approx_contours:
                # Scale points
                points = approx.reshape(-1, 2)
                # points[:, 0] = points[:, 0]
                # points[:, 1] = points[:, 1]
                points = points.tolist()
                if len(points) < 3:
                    continue
                points.append(points[0])

                # Create shape
                shape = Shape(flags={})
                for point in points:
                    point[0] = int(point[0])
                    point[1] = int(point[1])
                    shape.add_point(QPointF(point[0], point[1]))
                shape.shape_type = ShapeType.POLYGON
                shape.closed = True
                shape.label = AutoLabelEditMode.OBJECT.value
                shape.update_shape_color()
                shape.selected = False
                shapes.append(shape)
        elif self.output_mode in (ShapeType.RECTANGLE, ShapeType.ROTATION):
            x_min = 100000000
            y_min = 100000000
            x_max = 0
            y_max = 0
            for approx in approx_contours:
                # Scale points
                points = approx.reshape(-1, 2)
                # points[:, 0] = points[:, 0]
                # points[:, 1] = points[:, 1]
                points = points.tolist()
                if len(points) < 3:
                    continue

                # Get min/max
                for point in points:
                    x_min = min(x_min, point[0])
                    y_min = min(y_min, point[1])
                    x_max = max(x_max, point[0])
                    y_max = max(y_max, point[1])

            # Create shape
            shape = Shape(flags={})
            shape.add_point(QPointF(x_min, y_min))
            shape.add_point(QPointF(x_max, y_min))
            shape.add_point(QPointF(x_max, y_max))
            shape.add_point(QPointF(x_min, y_max))
            shape.shape_type = self.output_mode
            shape.closed = True
            shape.label = AutoLabelEditMode.OBJECT.value
            shape.selected = False
            shape.update_shape_color()
            if self.clip_net is not None and self.classes:
                img = image[y_min:y_max, x_min:x_max]
                out = self.clip_net(img, self.classes)
                shape.cache_label = self.classes[int(np.argmax(out))]
            shapes.append(shape)

        return shapes
