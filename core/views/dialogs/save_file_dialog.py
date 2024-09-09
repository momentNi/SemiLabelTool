import os

from PyQt5.QtWidgets import QFileDialog

from core.configs.constants import Constants
from core.configs.core import CORE
from core.dto.label_file import LabelFile


class SaveFileDialog(QFileDialog):
    def __init__(self, *args, **kwargs):
        super(SaveFileDialog, self).__init__(*args, **kwargs)
        self.setOption(self.DontConfirmOverwrite, False)
        self.setOption(self.DontUseNativeDialog, False)
        self.setAcceptMode(self.AcceptSave)
        self.setDefaultSuffix(LabelFile.suffix[1:])
        self.setWindowTitle(f"{Constants.APP_NAME} - Choose File")
        self.setDirectory(self.get_directory())
        self.setNameFilter(f"Label files (*{LabelFile.suffix})")

    @staticmethod
    def get_directory():
        if CORE.Variable.output_dir:
            return CORE.Variable.output_dir
        elif CORE.Variable.current_file_full_path:
            return os.path.dirname(CORE.Variable.current_file_full_path)
        else:
            return "."

    def get_save_file_name(self):
        basename = os.path.basename(os.path.splitext(CORE.Variable.current_file_full_path)[0])
        if CORE.Variable.output_dir:
            default_label_file_name = os.path.join(CORE.Variable.output_dir, basename + LabelFile.suffix)
        elif CORE.Variable.current_file_full_path:
            default_label_file_name = os.path.join(os.path.dirname(CORE.Variable.current_file_full_path),
                                                   basename + LabelFile.suffix)
        else:
            default_label_file_name = os.path.join(".", basename + LabelFile.suffix)
        filename = self.getSaveFileName(
            CORE.Object.main_window,
            "Choose File",
            str(default_label_file_name),
            f"Label files (*{LabelFile.suffix})"
        )
        if isinstance(filename, tuple):
            filename, _ = filename
        return filename
