from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt

from core.configs.core import CORE
from core.views.dialogs.brightness_contrast_dialog import BrightnessContrastDialog
from core.views.dialogs.cross_line_style_dialog import CrossLineStyleDialog
from utils.image import img_data_to_pil


def set_brightness_contrast():
    dialog = BrightnessContrastDialog(img_data_to_pil(CORE.Variable.image_data))
    brightness, contrast = CORE.Variable.brightness_contrast_map.get(CORE.Variable.current_file_full_path, (None, None))
    if brightness is not None:
        dialog.slider_brightness.setValue(brightness)
    if contrast is not None:
        dialog.slider_contrast.setValue(contrast)
    dialog.exec_()

    brightness = dialog.slider_brightness.value()
    contrast = dialog.slider_contrast.value()
    CORE.Variable.brightness_contrast_map[CORE.Variable.current_file_full_path] = (brightness, contrast)


def set_cross_line():
    dialog = CrossLineStyleDialog(CORE.Object.canvas.cross_line)
    if dialog.exec_() == QtWidgets.QDialog.Accepted:
        settings = dialog.get_settings()
        need_show = settings["need_show"]
        width = settings["width"]
        color = settings["color"]
        opacity = settings["opacity"]
        CORE.Object.canvas.set_cross_line_style(need_show, width, color, opacity)


def hide_selected_polygons():
    for index, item in enumerate(CORE.Object.label_list_widget):
        if item.shape().is_selected:
            item.setCheckState(Qt.Unchecked)
            CORE.Variable.selected_polygon_stack.append(index)
            CORE.Object.label_list_widget[index].shape().is_visible = False


def show_hidden_polygons():
    while len(CORE.Variable.selected_polygon_stack) > 0:
        index = CORE.Variable.selected_polygon_stack.pop()
        item = CORE.Object.label_list_widget.item_at_index(index)
        item.setCheckState(Qt.Checked)
        CORE.Object.label_list_widget[index].shape().is_visible = True
