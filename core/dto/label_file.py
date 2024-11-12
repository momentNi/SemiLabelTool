import base64
import json
import os

import utils
from core.configs.constants import Constants
from core.dto.enums import ShapeType
from core.dto.exceptions import LabelFileError
from utils.label_converter import LabelConverter
from utils.logger import logger


class LabelFile:
    suffix = ".json"

    def __init__(self, filename=None, image_dir=None):
        self.flags = {}
        self.shapes = []
        self.image_path = None
        self.image_data = None
        self.image_dir = image_dir
        if filename is not None:
            self.load(filename)
        self.filename = filename
        self.other_data = {}

    @staticmethod
    def is_label_file(filename):
        return os.path.splitext(filename)[1].lower() == LabelFile.suffix

    @staticmethod
    def _check_image_height_and_width(image_data, image_height, image_width):
        img_arr = utils.image.img_b64_to_arr(image_data)
        if image_height is not None and img_arr.shape[0] != image_height:
            logger.warning("image_height does not match with image_data or image_path, so getting image_height from actual image.")
            image_height = img_arr.shape[0]
        if image_width is not None and img_arr.shape[1] != image_width:
            logger.warning("image_width does not match with image_data or image_path, so getting image_width from actual image.")
            image_width = img_arr.shape[1]
        return image_height, image_width

    @staticmethod
    def load_image_file(filename, default=None):
        try:
            with open(filename, "rb") as f:
                return f.read()
        except IOError:
            logger.error(f"Failed opening image file: {filename}")
        return default

    def load(self, filename):
        keys = ["version", "imageData", "imagePath", "shapes", "flags", "imageHeight", "imageWidth"]
        shape_keys = ["label", "score", "points", "group_id", "is_difficult", "shape_type", "flags", "description", "attributes", "kie_linking"]
        try:
            with open(filename, "r", encoding='utf-8') as f:
                data = json.load(f)
            version = data.get("version")
            if version is None:
                logger.warning(f"Loading JSON file ({filename}) of unknown version")

            data["imagePath"] = os.path.basename(data["imagePath"])
            if data["imageData"] is not None:
                self.image_data = base64.b64decode(data["imageData"])
            else:
                if self.image_dir:
                    image_path = os.path.join(self.image_dir, data["imagePath"])
                else:
                    image_path = os.path.join(os.path.dirname(filename), data["imagePath"])
                self.image_data = self.load_image_file(image_path)
            flags = data.get("flags") or {}
            image_path = data["imagePath"]
            self._check_image_height_and_width(
                image_data=base64.b64encode(self.image_data).decode("utf-8"),
                image_height=data.get("imageHeight"),
                image_width=data.get("imageWidth"),
            )
            shapes = [
                {
                    "label": shape["label"],
                    "score": shape.get("score", None),
                    "points": shape["points"],
                    "shape_type": shape.get("shape_type", ShapeType.POLYGON.name),
                    "flags": shape.get("flags", {}),
                    "group_id": shape.get("group_id"),
                    "description": shape.get("description"),
                    "is_difficult": shape.get("is_difficult", False),
                    "attributes": shape.get("attributes", {}),
                    "kie_linking": shape.get("kie_linking", []),
                    "other_data": {k: v for k, v in shape.items() if k not in shape_keys},
                }
                for shape in data["shapes"]
            ]
            for i, s in enumerate(data["shapes"]):
                if ShapeType.ROTATION == s.get("shape_type", ShapeType.POLYGON.name):
                    shapes[i]["direction"] = s.get("direction", 0)
        except Exception as e:
            logger.error(e)
            raise LabelFileError(e) from e

        other_data = {}
        for key, value in data.items():
            if key not in keys:
                other_data[key] = value

        # Add new fields if not available
        other_data["text"] = other_data.get("text", "")

        # Only replace data after everything is loaded.
        self.flags = flags
        self.shapes = shapes
        self.image_path = image_path
        self.filename = filename
        self.other_data = other_data

    def save(self, filename=None, shapes=None, image_path=None, image_height=None, image_width=None, image_data=None, other_data=None, flags=None):
        if image_data is not None:
            image_data = base64.b64encode(image_data).decode("utf-8")
            image_height, image_width = self._check_image_height_and_width(image_data, image_height, image_width)

        if other_data is None:
            other_data = {}
        if flags is None:
            flags = {}
        for i, shape in enumerate(shapes):
            if ShapeType.RECTANGLE == shape["shape_type"]:
                sorted_box = LabelConverter.calculate_bounding_box(shape["points"])
                x_min, y_min, x_max, y_max = sorted_box
                shape["points"] = [
                    [x_min, y_min],
                    [x_max, y_min],
                    [x_max, y_max],
                    [x_min, y_max],
                ]
                shapes[i] = shape
        data = {
            "version": Constants.APP_VERSION,
            "flags": flags,
            "shapes": shapes,
            "imagePath": image_path,
            "imageData": image_data,
            "imageHeight": image_height,
            "imageWidth": image_width,
        }

        for key, value in other_data.items():
            if key in data:
                logger.error(f"Not expected key in other_data: {key}")
                continue
            data[key] = value
        try:
            with open(filename, "w") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self.filename = filename
        except Exception as e:
            raise LabelFileError(e) from e
