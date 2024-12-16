import os

from PyQt5.QtWidgets import QFileDialog

from core.configs.constants import Constants
from core.configs.core import CORE


class UploadCustomModelDialog(QFileDialog):
    def __init__(self):
        super(UploadCustomModelDialog, self).__init__(CORE.Object.main_window)
        self.config_file_path = None

        self.setModal(True)
        self.setWindowTitle(self.tr("Custom Model"))
        self.setFileMode(QFileDialog.ExistingFile)
        self.setNameFilter("Config files (*.yaml)")
        self.setWindowTitle(f"{Constants.APP_NAME} - Choose config file of new model")
        self.setWindowFilePath(os.path.dirname(CORE.Variable.current_file_full_path) if CORE.Variable.current_file_full_path else ".")
        self.setViewMode(QFileDialog.Detail)
        if self.exec_():
            filename = self.selectedFiles()[0]
            if filename:
                self.config_file_path = filename

    def get_upload_config_path(self):
        return self.config_file_path
