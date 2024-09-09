import base64
import json
import os

import utils
from utils.logger import logger


class LabelFileError(Exception):
    pass


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
            logger.error(
                "image_height does not match with image_data or image_path, so getting image_height from actual image.")
            image_height = img_arr.shape[0]
        if image_width is not None and img_arr.shape[1] != image_width:
            logger.error(
                "image_width does not match with image_data or image_path, so getting image_width from actual image.")
            image_width = img_arr.shape[1]
        return image_height, image_width

    def load_image_file(self, filename, default=None):
        try:
            with open(filename, "rb") as f:
                self.image_data = f.read()
        except IOError:
            logger.error(f"Failed opening image file: {filename}")
            self.image_data = default

    def load(self, filename):
        keys = ["version", "imageData", "imagePath", "shapes", "flags", "imageHeight", "imageWidth"]
        shape_keys = ["label", "score", "points", "group_id", "difficult", "shape_type", "flags", "description",
                      "attributes", "kie_linking"]
        try:
            with open(filename, "r", encoding='utf-8') as f:
                data = json.load(f)
            version = data.get("version")
            if version is None:
                logger.warning(f"Loading JSON file ({filename}) of unknown version")

            data["imagePath"] = os.path.basename(data["imagePath"])
            if data["imageData"] is not None:
                image_data = base64.b64decode(data["imageData"])
            else:
                # relative path from label file to relative path from cwd
                if self.image_dir:
                    image_path = os.path.join(self.image_dir, data["imagePath"])
                else:
                    image_path = os.path.join(os.path.dirname(filename), data["imagePath"])
                self.load_image_file(image_path)
            flags = data.get("flags") or {}
            image_path = data["imagePath"]
            self._check_image_height_and_width(
                base64.b64encode(self.image_data).decode("utf-8"),
                data.get("imageHeight"),
                data.get("imageWidth"),
            )
            shapes = [
                {
                    "label": s["label"],
                    "score": s.get("score", None),
                    "points": s["points"],
                    "shape_type": s.get("shape_type", "polygon"),
                    "flags": s.get("flags", {}),
                    "group_id": s.get("group_id"),
                    "description": s.get("description"),
                    "difficult": s.get("difficult", False),
                    "attributes": s.get("attributes", {}),
                    "kie_linking": s.get("kie_linking", []),
                    "other_data": {
                        k: v for k, v in s.items() if k not in shape_keys
                    },
                }
                for s in data["shapes"]
            ]
            for i, s in enumerate(data["shapes"]):
                if s.get("shape_type", "polygon") == "rotation":
                    shapes[i]["direction"] = s.get("direction", 0)
        except Exception as e:
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
