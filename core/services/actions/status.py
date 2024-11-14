from PyQt5 import QtWidgets

from core.configs.core import CORE
from core.services.actions.files import load_file
from core.views.dialogs.annotation_box_dialog import AnnotationBoxDialog
from core.views.dialogs.label_overview_dialog import LabelOverviewDialog
from core.views.dialogs.shape_overview_dialog import ShapeOverviewDialog


def show_label_overview():
    if CORE.Variable.current_file_full_path:
        LabelOverviewDialog()


def show_shape_overview():
    if CORE.Variable.current_file_full_path:
        ShapeOverviewDialog()


def show_box_settings():
    modify_label_dialog = AnnotationBoxDialog()
    result = modify_label_dialog.exec_()
    if result == QtWidgets.QDialog.Accepted:
        load_file(CORE.Variable.current_file_full_path)
