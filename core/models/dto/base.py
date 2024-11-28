import os
import pathlib
from abc import abstractmethod
from importlib import resources
from urllib import request
from urllib.parse import urlparse

import onnx
import yaml
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QProgressDialog

from core.configs.core import CORE
from core.models import configs
from utils.logger import logger


class AutoLabelingResult:
    def __init__(self, shapes, replace=True):
        """Initialize AutoLabelingResult

        Args:
            shapes (List[Shape]): List of shapes to add to the canvas.
            replace (bool, optional): Replaces all current shapes with
            new shapes. Defaults to True.
        """

        self.shapes = shapes
        self.replace = replace


class Model:
    def __init__(self, name, label, platform, model_type, config_path):
        # model name, unique identifier
        self.name = name
        # display name
        self.label = label
        # OD or SEG, determine which kind of model it is
        self.platform = platform
        # YOLOv10, YOLOv9, ... determine which Model DTO needs to be loaded
        self.model_type = model_type
        # other configs
        self.config_path = config_path
        self.configs = {}
        # Core model weight file for prediction.
        self.model = None
        self.output_mode = None

        self.download_progress_dialog = None

        try:
            if self.config_path.startswith(":/"):
                # Config file is in resources
                config_file_name = self.config_path[2:]
                with resources.open_text(configs, config_file_name) as f:
                    self.configs = yaml.safe_load(f)
                self.config_path = os.path.join(os.path.abspath(__file__), '../../configs', config_file_name)
            else:
                # Config file is in local file system
                with open(self.config_path, "r", encoding="utf-8") as f:
                    self.configs = yaml.safe_load(f)
                self.config_path = os.path.normpath(os.path.abspath(config_path))
        except FileNotFoundError:
            logger.error(f"Config file not found: {self.config_path}")

    @staticmethod
    def is_valid_config(config_dict):
        return "name" in config_dict and "label" in config_dict and "platform" in config_dict and "model_type" in config_dict and "config_path" in config_dict

    def fetch_model(self, field_name):
        model_path: str = self.configs[field_name]
        if model_path.startswith(("http://", "https://")):
            # URL path
            abs_path = self.download_model_by_url(model_path)
        else:
            # local file path
            abs_path = self.get_model_by_path(model_path)
        return abs_path

    def download_model_by_url(self, url):
        filename = os.path.basename(urlparse(url).path)
        home_dir = os.path.expanduser("~")
        download_dir_path = os.path.abspath(os.path.join(home_dir, "semi_label_data"))
        model_abs_path = os.path.abspath(os.path.join(download_dir_path, "models", self.name, filename))

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
                    return model_abs_path
            else:
                return model_abs_path
        pathlib.Path(model_abs_path).parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"Downloading {filename} to {model_abs_path}")
        try:
            request.urlretrieve(url=url, filename=model_abs_path, reporthook=self.__progress_hook)
        except Exception as e:
            logger.error(f"Could not download {url}: {e}")
            return None

        return model_abs_path

    def get_model_by_path(self, path):
        # Relative path to executable or absolute path?
        model_abs_path = os.path.abspath(path)
        if os.path.exists(model_abs_path):
            return model_abs_path
        else:
            config_folder = os.path.dirname(self.config_path)
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

    def __str__(self):
        return f"Model: {self.name} (label={self.label}, platform={self.platform}, type={self.model_type}, config_path={self.config_path}, configs={self.configs})"
