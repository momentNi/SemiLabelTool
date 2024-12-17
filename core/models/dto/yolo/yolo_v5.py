from core.models.dto.yolo.yolo_v9 import YOLOv9


class YOLOv5(YOLOv9):
    def __init__(self, name, label, platform, model_type, config_path):
        super().__init__(name, label, platform, model_type, config_path)

    def unload(self):
        del self.net
