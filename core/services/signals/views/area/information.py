from PyQt5.QtCore import Qt

from core.configs.core import CORE
from core.dto.enums import CanvasMode
from core.dto.label_list_widget_item import LabelListWidgetItem
from core.services.actions import files as files_action
from core.services.system import set_dirty


def label_selection_changed():
    if not CORE.Variable.has_selection_slot:
        return
    if CORE.Object.canvas.canvas_mode == CanvasMode.EDIT:
        selected_shapes = []
        for item in CORE.Object.label_list_widget.selected_items():
            selected_shapes.append(item.shape())
        if selected_shapes:
            CORE.Object.canvas.select_shapes(selected_shapes)
        else:
            CORE.Object.canvas.deselect_shape()


def label_item_changed(item: LabelListWidgetItem):
    shape = item.shape()
    CORE.Object.canvas.set_shape_visible(shape, item.checkState() == Qt.Checked)


def label_order_changed():
    set_dirty()
    CORE.Object.canvas.load_shapes([item.shape() for item in CORE.Object.label_list_widget])


def file_search_changed():
    files_action.load_image_folder(
        dir_path=CORE.Variable.last_open_dir_path,
        pattern=CORE.Object.info_file_search_widget.text(),
        need_load=False
    )
