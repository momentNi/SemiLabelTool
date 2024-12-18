import os
import pathlib
from abc import abstractmethod, ABCMeta
from importlib import resources
from typing import Optional, List
from urllib import request
from urllib.parse import urlparse

import onnx
import yaml
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QProgressDialog

from core.configs.constants import Constants
from core.configs.core import CORE
from core.dto.enums import Platform
from core.dto.shape import Shape
from core.models import configs
from utils.logger import logger


class AutoLabelingResult:
    def __init__(self, model: str, shapes: List[Shape], replace: bool = True):
        """Initialize AutoLabelingResult

        Args:
            model (str): The name of the model who predicts the label.
            shapes (List[Shape]): List of shapes to add to the canvas.
            replace (bool, optional): Replaces all current shapes with
            new shapes. Defaults to True.
        """
        self.model = model
        self.shapes = shapes
        self.replace = replace


class ModelInfo:
    def __init__(self, name, label, platform, model_type, config_path):
        # model name, unique identifier
        self.name: str = name
        # display name
        self.label: str = label
        # OD or SEG, determine which kind of model it is
        self.platform: Platform = platform
        # YOLOv10, YOLOv9, ... determine which Model DTO needs to be loaded
        self.model_type: str = model_type
        # other configs
        self.config_path: str = config_path
        # Core model weight file for prediction.
        self.weight: Optional[Model] = None

    def __str__(self):
        return f"ModelInfo(label={self.label}, platform={self.platform.value}, type={self.model_type}, config_path={self.config_path}, weight={self.weight})"

    @staticmethod
    def validate_config(config_dict) -> Optional[str]:
        required_keys = ['name', 'label', 'platform', 'model_type', 'config_path']
        for key in required_keys:
            if key not in config_dict:
                return key
        if config_dict['model_type'] not in Constants.VALID_CUSTOM_MODEL_TYPE:
            return config_dict['model_type']
        return None


class Model(metaclass=ABCMeta):
    def __init__(self, model_info: ModelInfo):
        self.model_info: ModelInfo = model_info
        self.configs: dict = {}
        self.output_mode: Optional[str] = None

        self.download_progress_dialog: Optional[QProgressDialog] = None

        if self.model_info.config_path.startswith(":/"):
            # Config file is in resources
            config_file_name = self.model_info.config_path[2:]
            try:
                with resources.open_text(configs, config_file_name) as f:
                    self.configs = yaml.safe_load(f)
            except FileNotFoundError:
                raise FileNotFoundError(self.model_info.config_path)
            self.model_info.config_path = os.path.join(os.path.abspath(__file__), '../../configs', config_file_name)
        else:
            # Config file is in local file system
            try:
                with open(self.model_info.config_path, "r", encoding="utf-8") as f:
                    self.configs = yaml.safe_load(f)
            except FileNotFoundError:
                raise FileNotFoundError(self.model_info.config_path)
            self.model_info.config_path = os.path.normpath(os.path.abspath(self.model_info.config_path))

    def fetch_model(self, field_name: str) -> Optional[str]:
        model_path: str = self.configs[field_name]
        if model_path.startswith(("http://", "https://")):
            # URL path
            abs_path = self.download_model_by_url(model_path)
        else:
            # local file path
            abs_path = self.get_model_by_path(model_path)
        return abs_path

    def download_model_by_url(self, url: str) -> Optional[str]:
        filename = os.path.basename(urlparse(url).path)
        home_dir = os.path.expanduser("~")
        download_dir_path = os.path.abspath(os.path.join(home_dir, "semi_label_data"))
        model_abs_path = os.path.abspath(os.path.join(download_dir_path, "models", self.model_info.name, filename))

        if not self.check_model_path(filename, model_abs_path):
            logger.info(f"Downloading {filename} to {model_abs_path}")
            try:
                _, headers = request.urlretrieve(url=url, filename=model_abs_path, reporthook=self.__progress_hook)
                if os.path.exists(model_abs_path) and str(headers.get("Content-Length")) == str(os.path.getsize(model_abs_path)):
                    return model_abs_path
                else:
                    logger.error("Downloaded file size does not match the expected size.")
                    return None
            except Exception as e:
                logger.error(f"Could not download {url}: {e}")
                return None
            finally:
                if self.download_progress_dialog is not None:
                    self.download_progress_dialog.close()
                    self.download_progress_dialog = None
        else:
            return model_abs_path

    @staticmethod
    def check_model_path(filename, model_abs_path):
        if os.path.exists(model_abs_path):
            if filename.lower().endswith(".onnx"):
                try:
                    onnx.checker.check_model(model_abs_path)
                except onnx.checker.ValidationError as e:
                    logger.warning(f"The model is invalid: {e}. Delete and re-download it.")
                    try:
                        os.remove(model_abs_path)
                    except Exception as e:
                        logger.warning("Could not delete: %s", str(e))
                else:
                    return True
            else:
                return True
        pathlib.Path(model_abs_path).parent.mkdir(parents=True, exist_ok=True)
        return False

    def get_model_by_path(self, path):
        # Relative path to executable or absolute path?
        model_abs_path = os.path.abspath(path)
        if os.path.exists(model_abs_path):
            return model_abs_path
        else:
            config_folder = os.path.dirname(self.model_info.config_path)
            model_abs_path = os.path.abspath(os.path.join(config_folder, path))
            if os.path.exists(model_abs_path):
                return model_abs_path
        return None

    @abstractmethod
    def predict_shapes(self, image, image_path=None, **kwargs) -> AutoLabelingResult:
        raise NotImplementedError

    @abstractmethod
    def unload(self):
        """
        Unload memory
        """
        raise NotImplementedError

    def __progress_hook(self, count, block_size, total_size):
        if self.download_progress_dialog is None:
            self.download_progress_dialog = QProgressDialog("Downloading model", "Abort", 0, total_size, CORE.Object.main_window)
            self.download_progress_dialog.setWindowModality(Qt.WindowModal)
            self.download_progress_dialog.setMinimumDuration(0)
        else:
            if self.download_progress_dialog.wasCanceled():
                return
            self.download_progress_dialog.setValue(count * block_size)
