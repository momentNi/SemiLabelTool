import os
from abc import abstractmethod, ABCMeta
from typing import Tuple

import cv2
import numpy as np
from PyQt5 import QtCore

from core.configs.constants import Constants
from core.dto.enums import ShapeType
from core.dto.shape import Shape
from core.models.dto.base import Model, AutoLabelingResult, ModelInfo
from core.models.utils.base import letterbox
from utils.image import qt_img_to_rgb_cv_img
from utils.logger import logger


class YOLO(Model, metaclass=ABCMeta):
    def __init__(self, model_info: ModelInfo):
        super().__init__(model_info)

        model_abs_path = self.fetch_model("model_path")
        if not model_abs_path or not os.path.isfile(model_abs_path):
            raise FileNotFoundError(model_abs_path)

        self.engine = self.configs.get("engine", "ort")
        if self.engine.lower() == "dnn":
            from core.models.engines import DnnBaseModel
            self.net: 'DnnBaseModel' = DnnBaseModel(model_abs_path, Constants.DEVICE)
            self.input_width = self.configs.get("input_width", 640)
            self.input_height = self.configs.get("input_height", 640)
        else:
            from core.models.engines import OnnxBaseModel
            self.net: 'OnnxBaseModel' = OnnxBaseModel(model_abs_path, Constants.DEVICE)
            _, _, self.input_height, self.input_width = self.net.get_input_shape()
            if not isinstance(self.input_width, int):
                self.input_width = self.configs.get("input_width", -1)
            if not isinstance(self.input_height, int):
                self.input_height = self.configs.get("input_height", -1)

        self.replace = True
        self.classes = self.configs.get("classes", [])
        self.stride = self.configs.get("stride", 32)
        self.anchors = self.configs.get("anchors", None)
        self.agnostic = self.configs.get("agnostic", False)
        self.show_boxes = self.configs.get("show_boxes", False)
        self.epsilon_factor = self.configs.get("epsilon_factor", 0.005)
        self.iou_threshold = self.configs.get("nms_threshold", 0.45)
        self.conf_threshold = self.configs.get("confidence_threshold", 0.25)
        self.filter_classes = self.configs.get("filter_classes", None)
        self.nc = len(self.classes)
        self.input_shape = (self.input_height, self.input_width)
        self.img_height = None
        self.img_width = None
        if self.anchors:
            self.nl = len(self.anchors)
            self.na = len(self.anchors[0]) // 2
            self.grid = [np.zeros(1)] * self.nl
            self.stride = (
                np.array([self.stride // 4, self.stride // 2, self.stride])
                if not isinstance(self.stride, list)
                else np.array(self.stride)
            )
            self.anchor_grid = np.asarray(self.anchors, dtype=np.float32).reshape(self.nl, -1, 2)
        if self.filter_classes:
            self.filter_classes = [i for i, item in enumerate(self.classes) if item in self.filter_classes]

        if isinstance(self.classes, dict):
            self.classes = list(self.classes.values())

    def set_conf_threshold(self, value):
        self.conf_threshold = value

    def set_iou_threshold(self, value):
        self.iou_threshold = value

    def set_is_preserve(self, value):
        self.replace = not value

    def inference(self, blob):
        if self.engine == "dnn":
            outputs = self.net.get_inference(blob=blob, extract=False)
            if not isinstance(outputs, (tuple, list)):
                outputs = [outputs]
        else:
            outputs = self.net.get_inference(blob=blob, extract=False)
        return outputs

    def pre_process(self, image, up_sample_mode="letterbox"):
        self.img_height, self.img_width = image.shape[:2]
        # Up sample
        if up_sample_mode == "resize":
            input_img = cv2.resize(image, (self.input_width, self.input_height))
        elif up_sample_mode == "letterbox":
            input_img = letterbox(image, self.input_shape)[0]
        elif up_sample_mode == "centercrop":
            m = min(self.img_height, self.img_width)
            top = (self.img_height - m) // 2
            left = (self.img_width - m) // 2
            cropped_img = image[top: top + m, left: left + m]
            input_img = cv2.resize(cropped_img, (self.input_width, self.input_height))
        else:
            logger.error(f"Unknown up sample mode: {up_sample_mode}")
            return None
        # Transpose
        input_img = input_img.transpose(2, 0, 1)
        # Expand
        input_img = input_img[np.newaxis, :, :, :].astype(np.float32)
        # Contiguous
        input_img = np.ascontiguousarray(input_img)
        # Norm
        blob = input_img / 255.0
        return blob

    @abstractmethod
    def post_process(self, predicts) -> Tuple:
        raise NotImplementedError

    def predict_shapes(self, image, image_path=None, **kwargs) -> AutoLabelingResult:
        if image is None:
            return AutoLabelingResult(self.model_info.name, [])
        try:
            image = qt_img_to_rgb_cv_img(image, image_path)
        except Exception as e:
            logger.warning("Could not inference model")
            logger.warning(e)
            return AutoLabelingResult(self.model_info.name, [])
        blob = self.pre_process(image, "letterbox")
        outputs = self.inference(blob)
        boxes, class_ids, scores = self.post_process(outputs)

        points = [[] for _ in range(len(boxes))]
        shapes = []

        for i, (box, class_id, score, point) in enumerate(zip(boxes, class_ids, scores, points)):
            x1, y1, x2, y2 = box.astype(float)
            shape = Shape(flags={})
            shape.add_point(QtCore.QPointF(x1, y1))
            shape.add_point(QtCore.QPointF(x2, y1))
            shape.add_point(QtCore.QPointF(x2, y2))
            shape.add_point(QtCore.QPointF(x1, y2))
            shape.shape_type = ShapeType.RECTANGLE
            shape.closed = True
            shape.label = str(self.classes[int(class_id)])
            shape.update_shape_color()
            shape.score = float(score)
            shape.selected = False
            shapes.append(shape)
        result = AutoLabelingResult(self.model_info.name, shapes, replace=self.replace)

        return result

    def unload(self):
        del self.net
