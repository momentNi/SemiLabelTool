from core.models.dto.base import ModelInfo
from core.models.dto.yolo.yolo_v7 import YOLOv7


class YOLOv6(YOLOv7):
    def __init__(self, model_info: ModelInfo):
        super().__init__(model_info)
