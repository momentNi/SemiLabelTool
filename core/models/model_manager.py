import os
import sys
from importlib import resources
from typing import Dict, Set

import yaml
from PyQt5.QtCore import QObject, pyqtSignal

from core.configs.constants import Constants
from core.dto.exceptions import ModelNotFoundError
from core.models import configs
from core.models.dto.base import Model
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
        try:
            with resources.open_text(configs, "default.yaml") as f:
                default_model_list = yaml.safe_load(f)
            for model_config in default_model_list:
                try:
                    model_dto = Model(**model_config)
                    self.model_dict[model_config["name"]] = model_dto
                    self.identify_model_platform(model_dto)
                except (FileNotFoundError, KeyError, ValueError):
                    show_critical_message("Error", f"Model {model_config['name']} not found.", trace=True)
                    continue
        except FileNotFoundError:
            show_critical_message("Error", "Error in loading default model configs.")
            return

    def add_custom_model(self, config_file_path):
        config_file_path = os.path.normpath(os.path.abspath(config_file_path))

        if not config_file_path or not os.path.isfile(config_file_path):
            show_critical_message("Error", f"Error in loading custom model: Invalid path: {config_file_path}.")
            return None

        with open(config_file_path, "r", encoding="utf-8") as f:
            model_config = yaml.safe_load(f)
        model_config["config_path"] = config_file_path
        missing_attr = Model.validate_config(model_config)
        if missing_attr is not None:
            show_critical_message("Error", f"model config miss core argument: {missing_attr}", trace=False)
            return None
        try:
            model_dto = Model(**model_config)
            if self.identify_model_platform(model_dto):
                self.model_dict[model_dto.name] = model_dto
                return model_dto.name
            else:
                return None
        except (FileNotFoundError, KeyError, ValueError):
            show_critical_message("Error", f"Model {model_config['name']} not found.", trace=True)
            return None

    def identify_model_platform(self, model_dto: Model):
        if model_dto.platform == "od":
            self.od_models.add(model_dto.name)
            return True
        elif model_dto.platform == "seg":
            self.seg_models.add(model_dto.name)
            return True
        else:
            show_critical_message("Error", f"Unknown platform: {model_dto.platform} Model config: {model_dto}", trace=False)
            return False

    def load_model_weight(self, name):
        if name not in self.model_dict:
            raise ModelNotFoundError(name)

        model_dto: Model = self.model_dict[name]

        # noinspection PyBroadException
        try:
            model_dto.weight = getattr(sys.modules[__name__], model_dto.model_type)(
                name=name,
                label=model_dto.label,
                platform=model_dto.platform,
                model_type=model_dto.model_type,
                config_path=model_dto.config_path
            )
        except AttributeError as e:
            show_critical_message("Error", f"Unknown model type: {e}. Valid types are: {Constants.VALID_CUSTOM_MODEL_TYPE}", trace=False)
            return False
        except FileNotFoundError as e:
            show_critical_message("Error", f"Critical file missing: {e}.", trace=False)
            return False
        except Exception:
            show_critical_message("Error", "Something went wrong.", trace=True)
            return False

        return model_dto.weight is not None

    def unload_model_weight(self, name):
        try:
            if name in self.model_dict:
                self.model_dict[name].unload()
        except NotImplementedError:
            logger.warning(f"Model {name} has not implemented `unload` method. Please implement it.")

    def active_models(self, platform: str, model_name: str):
        load_result = False
        try:
            if platform == "od":
                if model_name in self.active_od_models:
                    self.active_od_models.remove(model_name)
                    self.unload_model_weight(model_name)
                load_result = self.load_model_weight(model_name)
                if load_result:
                    self.active_od_models.add(model_name)
            elif platform == "seg":
                if model_name in self.active_seg_models:
                    self.active_seg_models.remove(model_name)
                    self.unload_model_weight(model_name)
                load_result = self.load_model_weight(model_name)
                if load_result:
                    self.active_seg_models.add(model_name)
            else:
                show_critical_message("Error", f"Unknown platform: {platform} when activating models.", trace=False)
        except ModelNotFoundError as e:
            show_critical_message("Error", f"Model {e} not found.", trace=False)
        return load_result

    def label_image(self, platform, image, filename=None):
        model_set = set()
        if platform == "od":
            model_set = self.active_od_models
        elif platform == "seg":
            model_set = self.active_seg_models
        try:
            result_list = []
            for name in model_set:
                model_dto = self.model_dict[name]
                if model_dto.weight is None:
                    self.load_model_weight(name)
                result_list.append(model_dto.weight.predict_shapes(image, filename))
            return result_list
        except (ModelNotFoundError, IndexError) as e:
            show_critical_message("Error", f"Model {e} not found.", trace=False)
