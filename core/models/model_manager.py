import os
from importlib import resources
from typing import Dict, List, Set

import yaml
from PyQt5.QtCore import QObject, pyqtSignal

from core.models import configs
from core.models.dto.base import Model
from core.models.dto.sam import SegmentAnything
from core.models.dto.yolo.yolo_v10 import YOLOv10
from core.services.system import show_critical_message
from utils.logger import logger


class ModelManager(QObject):
    model_configs_changed_signal = pyqtSignal(list)

    def __init__(self):
        super().__init__()
        self.model_dict: Dict[str, Model] = {}
        self.od_models: Set[str] = set()
        self.seg_models: Set[str] = set()
        self.active_od_models: Set[str] = set()
        self.active_seg_models: Set[str] = set()

        self.add_default_model()

    def add_default_model(self):
        default_model_list = []
        try:
            with resources.open_text(configs, "default.yaml") as f:
                default_model_list = yaml.safe_load(f)
        except IOError:
            show_critical_message("Error", "Error in loading default model configs.")
        for model_config in default_model_list:
            if not Model.is_valid_config(model_config):
                show_critical_message("Error", f"Error in loading model configs: {model_config}")
                continue
            model_dto = Model(**model_config)
            self.model_dict[model_config["name"]] = model_dto
            self.identify_model_platform(model_dto)

    def add_custom_model(self, config_file_path):
        config_file_path = os.path.normpath(os.path.abspath(config_file_path))

        if not config_file_path or not os.path.isfile(config_file_path):
            show_critical_message("Error", f"Error in loading custom model: Invalid path: {config_file_path}.")
            return

        with open(config_file_path, "r", encoding="utf-8") as f:
            model_config = yaml.safe_load(f)
        if not Model.is_valid_config(model_config):
            show_critical_message("Error", f"Error in loading model configs: {model_config}")
            return
        model_dto = Model(**model_config)
        if model_dto.name in self.model_dict:
            logger.warning(f"Model {model_config["name"]} already exists, replacing it")
        self.model_dict[model_dto.name] = model_dto
        self.identify_model_platform(model_dto)

    def identify_model_platform(self, model_dto: Model):
        if model_dto.platform == "od":
            self.od_models.add(model_dto.name)
        elif model_dto.platform == "seg":
            self.seg_models.add(model_dto.name)
        else:
            show_critical_message("Error", f"Unknown platform: {model_dto.platform} Model config: {model_dto}", trace=False)

    def load_model_weight(self, name):
        if name not in self.model_dict:
            logger.error(f"Model {name} not found.")
            return False
        if name in self.active_od_models or name in self.active_seg_models:
            logger.error(f"Model {name} is using. Please unload it before modifying its weight.")
            return False
        model_dto = self.model_dict[name]
        if model_dto.model_type == "yolov10":
            try:
                model_dto.model = YOLOv10(name=name, label=model_dto.label, platform=model_dto.platform, model_type=model_dto.model_type, config_path=model_dto.config_path, task="det")
            except Exception as e:
                show_critical_message("Error", f"Error loading model: {e}")
                return False
        elif model_dto.model_type == "sam":
            try:
                model_dto.model = SegmentAnything(name=name, label=model_dto.label, platform=model_dto.platform, model_type=model_dto.model_type, config_path=model_dto.config_path)
            except Exception as e:
                show_critical_message("Error", f"Error loading model: {e}")
                return False
        else:
            show_critical_message("Error", f"Unknown model type: {model_dto.model_type}")
            return False
        return True

    def unload_model_weight(self, name):
        if name in self.model_dict:
            self.model_dict[name].unload()

    def active_models(self, platform: str, models: List[str]):
        if platform == "od":
            self.active_od_models.clear()
            for name in models:
                self.load_model_weight(name)
                self.active_od_models.add(name)
        elif platform == "seg":
            self.active_seg_models.clear()
            for name in models:
                self.active_seg_models.add(name)
                self.load_model_weight(name)
        else:
            show_critical_message("Error", f"Unknown platform: {platform} when activating models.", trace=False)

    def label_image(self, platform, image, filename=None):
        if platform == "od":
            try:
                for name in self.active_od_models:
                    model_dto = self.model_dict[name]
                    if model_dto.model is None:
                        self.load_model_weight(name)
                    result = model_dto.model.predict_shapes(image, filename)
                    return result
            except Exception:
                show_critical_message("Error", f"Error in predicting shapes.")
