from core.configs.core import CORE
from core.views.dialogs.label_overview_dialog import LabelOverviewDialog
from core.views.dialogs.shape_overview_dialog import ShapeOverviewDialog


def show_label_overview():
    if CORE.Variable.current_file_full_path:
        LabelOverviewDialog()


def show_shape_overview():
    if CORE.Variable.current_file_full_path:
        ShapeOverviewDialog()


def show_label_manager():
    pass
