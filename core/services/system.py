import os

from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt

from core.configs.constants import Constants
from core.configs.core import CORE
from core.dto.enums import ZoomMode, CanvasMode, ShapeType
from core.services.actions import files
from utils.function import find_most_similar_label
from utils.logger import logger


def set_dirty():
    CORE.Action.undo.setEnabled(CORE.Object.canvas.is_shape_restorable)

    if CORE.Variable.settings.get("auto_save", True):
        label_file = f"{os.path.splitext(CORE.Variable.label_file.image_path)[0]}.json"
        if CORE.Variable.output_dir:
            label_file = os.path.join(CORE.Variable.output_dir, os.path.basename(label_file))
        files.save_labels(label_file)
        return
    CORE.Variable.is_dirty = True
    CORE.Action.save_file.setEnabled(True)
    title = Constants.APP_NAME
    if CORE.Variable.current_file_full_path is not None:
        title = f"{title} - {CORE.Variable.current_file_full_path}"
    CORE.Object.main_window.setWindowTitle(title)


def set_clean():
    CORE.Variable.is_dirty = False
    CORE.Action.save_file.setEnabled(False)
    # TODO CORE.Action.union_selection.setEnabled(False)
    CORE.Action.create_mode.setEnabled(True)
    CORE.Action.create_rectangle_mode.setEnabled(True)
    CORE.Action.create_rotation_mode.setEnabled(True)
    CORE.Action.create_circle_mode.setEnabled(True)
    CORE.Action.create_line_mode.setEnabled(True)
    CORE.Action.create_point_mode.setEnabled(True)
    CORE.Action.create_line_strip_mode.setEnabled(True)

    title = Constants.APP_NAME
    if CORE.Variable.current_file_full_path is not None:
        title = f"{title} - {CORE.Variable.current_file_full_path}"
    CORE.Object.main_window.setWindowTitle(title)

    if has_label_file():
        CORE.Action.delete_file.setEnabled(True)
    else:
        CORE.Action.delete_file.setEnabled(False)


def reset_state():
    CORE.Object.label_list_widget.clear()
    CORE.Variable.current_file_full_path = None
    CORE.Variable.label_file = None
    CORE.Object.canvas.reset_canvas()
    CORE.Object.label_filter_combo_box.combo_box.clear()


def has_label_file():
    if CORE.Variable.current_file_full_path is None:
        return False

    label_file = get_label_file()
    return os.path.exists(label_file)


def get_label_file():
    if CORE.Variable.current_file_full_path.lower().endswith(".json"):
        label_file = CORE.Variable.current_file_full_path
    else:
        label_file = os.path.splitext(CORE.Variable.current_file_full_path)[0] + ".json"
    return label_file


def toggle_drawing_sensitive(drawing=True):
    CORE.Action.edit_object.setEnabled(not drawing)
    CORE.Action.undo_last_point.setEnabled(drawing)
    CORE.Action.undo.setEnabled(not drawing)
    CORE.Action.delete_polygon.setEnabled(not drawing)


def on_item_description_change():
    description = CORE.Object.item_description.toPlainText()
    logger.info(f"description: {description}")
    if CORE.Object.canvas.current is not None:
        CORE.Object.canvas.current.description = description
    elif CORE.Object.canvas.canvas_mode == CanvasMode.EDIT and len(CORE.Object.canvas.selected_shapes) == 1:
        CORE.Object.canvas.selected_shapes[0].description = description
    else:
        CORE.Variable.label_file.other_data["image_description"] = description
    set_dirty()


def set_zoom(value):
    CORE.Action.fit_width.setChecked(False)
    CORE.Action.fit_window.setChecked(False)
    CORE.Object.canvas.zoom_mode = ZoomMode.MANUAL_ZOOM
    CORE.Object.zoom_widget.setValue(value)
    CORE.Object.canvas.zoom_history[CORE.Variable.current_file_full_path] = (CORE.Object.canvas.zoom_mode, value)


def adjust_scale(initial=False):
    value = CORE.Object.canvas.scaler[ZoomMode.FIT_WINDOW if initial else CORE.Variable.zoom_mode]()
    value = int(100 * value)
    CORE.Object.zoom_widget.setValue(value)
    CORE.Object.canvas.zoom_history[CORE.Variable.current_file_full_path] = (CORE.Object.canvas.zoom_mode, 100)


def scale_fit_window():
    """Figure out the size of the pixmap to fit the main widget."""
    e = 2.0  # So that no scrollbars are generated.
    w1 = CORE.Object.scroll_area.width() - e
    h1 = CORE.Object.scroll_area.height() - e
    wh_ratio1 = w1 / h1
    # Calculate a new scale value based on the pixmap's aspect ratio.
    w2 = CORE.Object.canvas.pixmap.width() - 0.0
    h2 = CORE.Object.canvas.pixmap.height() - 0.0
    wh_ratio2 = w2 / h2
    return w1 / w2 if wh_ratio2 >= wh_ratio1 else h1 / h2


def scale_fit_width():
    # The epsilon does not seem to work too well here.
    w = CORE.Object.scroll_area.width() - 2.0
    return w / CORE.Object.canvas.pixmap.width()


def load_flags(flags: dict):
    CORE.Object.flag_widget.clear()
    for key, flag in flags.items():
        item = QtWidgets.QListWidgetItem(key)
        item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
        item.setCheckState(Qt.Checked if flag else Qt.Unchecked)
        CORE.Object.flag_widget.addItem(item)


def update_combo_box():
    # Get the unique labels and add them to the Combobox.
    labels_list = []
    for item in CORE.Object.label_list_widget:
        label = item.shape().label
        labels_list.append(str(label))
    unique_labels_list = list(set(labels_list))

    # Add a null row for showing all the labels
    unique_labels_list.append("")
    unique_labels_list.sort()
    CORE.Object.label_filter_combo_box.update_items(unique_labels_list)


def set_item_description(enable: bool):
    CORE.Object.item_description.textChanged.disconnect()
    if enable:
        CORE.Object.item_description.setDisabled(False)
        if len(CORE.Object.canvas.selected_shapes) == 1:
            new_text = CORE.Object.canvas.selected_shapes[0].description
        else:
            new_text = CORE.Variable.label_file.other_data.get("image_description", "")

    else:
        CORE.Object.item_description.setDisabled(True)
        new_text = ""
    CORE.Object.item_description.setPlainText(new_text)
    CORE.Object.item_description.textChanged.connect(on_item_description_change)


def toggle_draw_mode(edit: bool, create_mode: ShapeType = ShapeType.RECTANGLE, disable_auto_labeling: bool = True):
    # TODO Disable auto labeling if needed
    # if disable_auto_labeling and self.auto_labeling_widget.auto_labeling_mode != AutoLabelingMode.NONE:
    #     self.clear_auto_labeling_marks()
    #     self.auto_labeling_widget.set_auto_labeling_mode(None)

    set_item_description(enable=False)

    CORE.Object.canvas.set_editing(edit)
    CORE.Object.canvas.create_mode = create_mode
    if edit:
        CORE.Action.create_mode.setEnabled(True)
        CORE.Action.create_rectangle_mode.setEnabled(True)
        CORE.Action.create_rotation_mode.setEnabled(True)
        CORE.Action.create_circle_mode.setEnabled(True)
        CORE.Action.create_line_mode.setEnabled(True)
        CORE.Action.create_point_mode.setEnabled(True)
        CORE.Action.create_line_strip_mode.setEnabled(True)
    else:
        CORE.Action.union_selection.setEnabled(False)
        if create_mode == ShapeType.POLYGON:
            CORE.Action.create_mode.setEnabled(False)
            CORE.Action.create_rectangle_mode.setEnabled(True)
            CORE.Action.create_rotation_mode.setEnabled(True)
            CORE.Action.create_circle_mode.setEnabled(True)
            CORE.Action.create_line_mode.setEnabled(True)
            CORE.Action.create_point_mode.setEnabled(True)
            CORE.Action.create_line_strip_mode.setEnabled(True)
        elif create_mode == ShapeType.RECTANGLE:
            CORE.Action.create_mode.setEnabled(True)
            CORE.Action.create_rectangle_mode.setEnabled(False)
            CORE.Action.create_rotation_mode.setEnabled(True)
            CORE.Action.create_circle_mode.setEnabled(True)
            CORE.Action.create_line_mode.setEnabled(True)
            CORE.Action.create_point_mode.setEnabled(True)
            CORE.Action.create_line_strip_mode.setEnabled(True)
        elif create_mode == ShapeType.LINE:
            CORE.Action.create_mode.setEnabled(True)
            CORE.Action.create_rectangle_mode.setEnabled(True)
            CORE.Action.create_rotation_mode.setEnabled(True)
            CORE.Action.create_circle_mode.setEnabled(True)
            CORE.Action.create_line_mode.setEnabled(False)
            CORE.Action.create_point_mode.setEnabled(True)
            CORE.Action.create_line_strip_mode.setEnabled(True)
        elif create_mode == ShapeType.POINT:
            CORE.Action.create_mode.setEnabled(True)
            CORE.Action.create_rectangle_mode.setEnabled(True)
            CORE.Action.create_rotation_mode.setEnabled(True)
            CORE.Action.create_circle_mode.setEnabled(True)
            CORE.Action.create_line_mode.setEnabled(True)
            CORE.Action.create_point_mode.setEnabled(False)
            CORE.Action.create_line_strip_mode.setEnabled(True)
        elif create_mode == ShapeType.CIRCLE:
            CORE.Action.create_mode.setEnabled(True)
            CORE.Action.create_rectangle_mode.setEnabled(True)
            CORE.Action.create_rotation_mode.setEnabled(True)
            CORE.Action.create_circle_mode.setEnabled(False)
            CORE.Action.create_line_mode.setEnabled(True)
            CORE.Action.create_point_mode.setEnabled(True)
            CORE.Action.create_line_strip_mode.setEnabled(True)
        elif create_mode == ShapeType.LINE_STRIP:
            CORE.Action.create_mode.setEnabled(True)
            CORE.Action.create_rectangle_mode.setEnabled(True)
            CORE.Action.create_rotation_mode.setEnabled(True)
            CORE.Action.create_circle_mode.setEnabled(True)
            CORE.Action.create_line_mode.setEnabled(True)
            CORE.Action.create_point_mode.setEnabled(True)
            CORE.Action.create_line_strip_mode.setEnabled(False)
        elif create_mode == ShapeType.ROTATION:
            CORE.Action.create_mode.setEnabled(True)
            CORE.Action.create_rectangle_mode.setEnabled(True)
            CORE.Action.create_rotation_mode.setEnabled(False)
            CORE.Action.create_circle_mode.setEnabled(True)
            CORE.Action.create_line_mode.setEnabled(True)
            CORE.Action.create_point_mode.setEnabled(True)
            CORE.Action.create_line_strip_mode.setEnabled(True)
        else:
            logger.error(f"Unsupported create_mode: {create_mode}")
            raise ValueError(f"Unsupported create_mode: {create_mode}")
    CORE.Action.edit_object.setEnabled(not edit)
    update_label_instruction()


def set_edit_mode():
    # TODO Disable auto labeling
    # self.clear_auto_labeling_marks()
    # self.auto_labeling_widget.set_auto_labeling_mode(None)

    toggle_draw_mode(True)
    set_item_description(True)
    update_label_instruction()


def update_label_instruction():
    logger.info(f"Current mode: {CORE.Object.canvas.canvas_mode}")
    # TODO 更新instruction部分的文字状态，可能需要信号介入，待实现


def validate_label(label):
    for i in range(CORE.Object.unique_label_list_widget.count()):
        label_i = CORE.Object.unique_label_list_widget.item(i).data(Qt.UserRole)
        if label_i == label:
            return True
    return False


def reset_attribute(text):
    valid_labels = list(CORE.Variable.attributes.keys())
    if text not in valid_labels:
        most_similar_label = find_most_similar_label(text, valid_labels)
        QtWidgets.QMessageBox.critical(
            CORE.Object.main_window,
            "Invalid label",
            f"<p><b>Invalid label '{text}' with validation type: {valid_labels}!\nReset the label as {most_similar_label}.</b></p>"
        )
        text = most_similar_label
    return text


def toggle_zoom_related_action(value: bool):
    CORE.Object.zoom_widget_action.setEnabled(value)
    CORE.Action.zoom_in.setEnabled(value)
    CORE.Action.zoom_out.setEnabled(value)
    CORE.Action.zoom_original.setEnabled(value)
    CORE.Action.fit_window.setEnabled(value)
    CORE.Action.fit_width.setEnabled(value)


def toggle_load_related_action(value: bool):
    CORE.Action.close.setEnabled(value)
    CORE.Action.create_mode.setEnabled(value)
    CORE.Action.create_rectangle_mode.setEnabled(value)
    CORE.Action.create_rotation_mode.setEnabled(value)
    CORE.Action.create_circle_mode.setEnabled(value)
    CORE.Action.create_line_mode.setEnabled(value)
    CORE.Action.create_point_mode.setEnabled(value)
    CORE.Action.create_line_strip_mode.setEnabled(value)
    CORE.Action.edit_object.setEnabled(value)
    CORE.Action.set_brightness_contrast.setEnabled(value)
