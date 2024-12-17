from core.models.dto.yolo.yolo_v7 import YOLOv7


class YOLOv6(YOLOv7):
    def __init__(self, name, label, platform, model_type, config_path):
        super().__init__(name, label, platform, model_type, config_path)

    def unload(self):
        del self.net
