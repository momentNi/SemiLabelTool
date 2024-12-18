from core.models.dto.base import ModelInfo
from core.models.dto.yolo.yolo_v9 import YOLOv9


class YOLOv8(YOLOv9):
    def __init__(self, model_info: ModelInfo):
        super().__init__(model_info)
