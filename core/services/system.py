import os
import traceback

from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt

from core.configs.constants import Constants
from core.configs.core import CORE
from core.dto.enums import ZoomMode, CanvasMode, ShapeType, AutoLabelEditMode, AutoLabelShapeType
from core.dto.exceptions import LabelFileError
from core.dto.label_file import LabelFile
from core.services.actions import files
from core.services.actions.edit import add_label
from utils.function import find_most_similar_label
from utils.logger import logger


def get_instruction_label():
    shortcuts = "<b>Shortcuts:</b> Previous(<b>A</b>), Next(<b>D</b>), Rectangle(<b>R</b>), Polygon(<b>P</b>), Rotation(<b>O</b>)"
    if CORE.Object.canvas is not None:
        return f"<b>Mode:</b> {CORE.Object.canvas.get_canvas_mode()} | {shortcuts}"
    else:
        return shortcuts


def set_dirty():
    CORE.Action.undo.setEnabled(CORE.Object.canvas.is_shape_restorable)
    if CORE.Variable.settings.get("auto_save", True):
        label_file = f"{os.path.splitext(CORE.Variable.image_path)[0]}.json"
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
    CORE.Action.union_selection.setEnabled(False)
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
    CORE.Variable.image_path = None
    CORE.Variable.image_data = None
    CORE.Variable.label_file = None
    CORE.Variable.other_data = {}
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


def get_label_file_list():
    label_file_list = []
    if not CORE.Variable.image_list and CORE.Variable.current_file_full_path:
        dir_path, filename = os.path.split(CORE.Variable.current_file_full_path)
        label_file = os.path.join(dir_path, os.path.splitext(filename)[0] + ".json")
        if os.path.exists(label_file):
            label_file_list = [label_file]
    elif CORE.Variable.image_list and not CORE.Variable.output_dir and CORE.Variable.current_file_full_path:
        file_list = os.listdir(os.path.dirname(CORE.Variable.current_file_full_path))
        for file_name in file_list:
            if not file_name.endswith(".json"):
                continue
            label_file_list.append(os.path.join(os.path.dirname(CORE.Variable.current_file_full_path), file_name))
    if CORE.Variable.output_dir:
        for file_name in os.listdir(CORE.Variable.output_dir):
            if not file_name.endswith(".json"):
                continue
            label_file_list.append(os.path.join(CORE.Variable.output_dir, file_name))
    return label_file_list


def toggle_drawing_sensitive(drawing=True):
    CORE.Action.edit_object.setEnabled(not drawing)
    CORE.Action.undo_last_point.setEnabled(drawing)
    CORE.Action.undo.setEnabled(not drawing)
    CORE.Action.delete_polygon.setEnabled(not drawing)


def on_item_description_change():
    description = CORE.Object.item_description.toPlainText()
    if CORE.Object.canvas.current is not None:
        CORE.Object.canvas.current.description = description
    elif CORE.Object.canvas.canvas_mode == CanvasMode.EDIT and len(CORE.Object.canvas.selected_shapes) == 1:
        CORE.Object.canvas.selected_shapes[0].description = description
    else:
        CORE.Variable.other_data["image_description"] = description
    set_dirty()


def set_zoom(value):
    CORE.Action.fit_width.setChecked(False)
    CORE.Action.fit_window.setChecked(False)
    CORE.Object.canvas.zoom_mode = ZoomMode.MANUAL_ZOOM
    CORE.Object.zoom_widget.setValue(value)
    CORE.Object.canvas.zoom_history[CORE.Variable.current_file_full_path] = (CORE.Object.canvas.zoom_mode, value)


def adjust_scale(initial=False):
    value = CORE.Object.canvas.scaler[ZoomMode.FIT_WINDOW if initial else CORE.Object.canvas.zoom_mode]()
    value = int(100 * value)
    CORE.Object.zoom_widget.setValue(value)
    CORE.Object.canvas.zoom_history[CORE.Variable.current_file_full_path] = (CORE.Object.canvas.zoom_mode, value)


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


def load_shapes(shapes, replace=True):
    CORE.Variable.has_selection_slot = False
    for shape in shapes:
        add_label(shape)
    CORE.Object.label_list_widget.clearSelection()
    CORE.Variable.has_selection_slot = True
    CORE.Object.canvas.load_shapes(shapes, replace=replace)


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
            new_text = CORE.Variable.other_data.get("image_description", "")

    else:
        CORE.Object.item_description.setDisabled(True)
        new_text = ""
    CORE.Object.item_description.setPlainText(new_text)
    CORE.Object.item_description.textChanged.connect(on_item_description_change)


def toggle_draw_mode(edit: bool, create_mode: ShapeType = ShapeType.RECTANGLE, disable_auto_labeling: bool = True):
    if disable_auto_labeling and CORE.Object.canvas.auto_labeling_mode != (AutoLabelEditMode.OFF, AutoLabelShapeType.OFF):
        CORE.Object.canvas.clear_auto_labeling_marks()
        CORE.Object.canvas.set_auto_labeling_mode(AutoLabelEditMode.OFF, AutoLabelShapeType.OFF)

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
        if ShapeType.POLYGON == create_mode:
            CORE.Action.create_mode.setEnabled(False)
            CORE.Action.create_rectangle_mode.setEnabled(True)
            CORE.Action.create_rotation_mode.setEnabled(True)
            CORE.Action.create_circle_mode.setEnabled(True)
            CORE.Action.create_line_mode.setEnabled(True)
            CORE.Action.create_point_mode.setEnabled(True)
            CORE.Action.create_line_strip_mode.setEnabled(True)
        elif ShapeType.RECTANGLE == create_mode:
            CORE.Action.create_mode.setEnabled(True)
            CORE.Action.create_rectangle_mode.setEnabled(False)
            CORE.Action.create_rotation_mode.setEnabled(True)
            CORE.Action.create_circle_mode.setEnabled(True)
            CORE.Action.create_line_mode.setEnabled(True)
            CORE.Action.create_point_mode.setEnabled(True)
            CORE.Action.create_line_strip_mode.setEnabled(True)
        elif ShapeType.LINE == create_mode:
            CORE.Action.create_mode.setEnabled(True)
            CORE.Action.create_rectangle_mode.setEnabled(True)
            CORE.Action.create_rotation_mode.setEnabled(True)
            CORE.Action.create_circle_mode.setEnabled(True)
            CORE.Action.create_line_mode.setEnabled(False)
            CORE.Action.create_point_mode.setEnabled(True)
            CORE.Action.create_line_strip_mode.setEnabled(True)
        elif ShapeType.POINT == create_mode:
            CORE.Action.create_mode.setEnabled(True)
            CORE.Action.create_rectangle_mode.setEnabled(True)
            CORE.Action.create_rotation_mode.setEnabled(True)
            CORE.Action.create_circle_mode.setEnabled(True)
            CORE.Action.create_line_mode.setEnabled(True)
            CORE.Action.create_point_mode.setEnabled(False)
            CORE.Action.create_line_strip_mode.setEnabled(True)
        elif ShapeType.CIRCLE == create_mode:
            CORE.Action.create_mode.setEnabled(True)
            CORE.Action.create_rectangle_mode.setEnabled(True)
            CORE.Action.create_rotation_mode.setEnabled(True)
            CORE.Action.create_circle_mode.setEnabled(False)
            CORE.Action.create_line_mode.setEnabled(True)
            CORE.Action.create_point_mode.setEnabled(True)
            CORE.Action.create_line_strip_mode.setEnabled(True)
        elif ShapeType.LINE_STRIP == create_mode:
            CORE.Action.create_mode.setEnabled(True)
            CORE.Action.create_rectangle_mode.setEnabled(True)
            CORE.Action.create_rotation_mode.setEnabled(True)
            CORE.Action.create_circle_mode.setEnabled(True)
            CORE.Action.create_line_mode.setEnabled(True)
            CORE.Action.create_point_mode.setEnabled(True)
            CORE.Action.create_line_strip_mode.setEnabled(False)
        elif ShapeType.ROTATION == create_mode:
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
    CORE.Object.instruction_part.setText(get_instruction_label())


def set_edit_mode():
    toggle_draw_mode(True)
    set_item_description(True)
    CORE.Object.instruction_part.setText(get_instruction_label())


def find_last_label() -> str:
    """
    Find the last label in the label list.
    Exclude labels for auto labeling.
    """
    # Get from dialog history
    last_label = CORE.Object.label_dialog.get_last_label()
    if last_label:
        return last_label

    # Get selected label from the label list
    items = CORE.Object.label_list_widget.selected_items()
    if items:
        shape = items[0].data(Qt.UserRole)
        return shape.label

    # Get the last label from the label list
    for item in reversed(CORE.Object.label_list_widget):
        shape = item.data(Qt.UserRole)
        if shape.label not in (AutoLabelEditMode.OBJECT.value, AutoLabelEditMode.ADD.value, AutoLabelEditMode.REMOVE.value):
            return shape.label

    # No label is found
    return ""


def update_attributes(i: int):
    def attribute_selection_changed(i, prop, combo):
        selected_option = combo.currentText()
        CORE.Object.canvas.shapes[i].attributes[prop] = selected_option
        save_attributes(CORE.Object.canvas.shapes)

    selected_options = {}
    target_shape = CORE.Object.canvas.shapes[i]
    target_label = target_shape.label
    target_attribute = target_shape.attributes
    current_attribute = CORE.Variable.attributes.get(target_label, {})
    # Clear the existing widgets from the QGridLayout
    grid_layout = QtWidgets.QGridLayout()
    # Repopulate the QGridLayout with the updated data
    for row, (prop, options) in enumerate(current_attribute.items()):
        property_label = QtWidgets.QLabel(prop)
        property_combo = QtWidgets.QComboBox()
        property_combo.addItems(options)
        property_combo.currentIndexChanged.connect(lambda _: attribute_selection_changed(i, prop, property_combo))
        grid_layout.addWidget(property_label, row, 0)
        grid_layout.addWidget(property_combo, row, 1)
        selected_options[prop] = options[0]
    # Ensure the scroll_area updates its contents
    grid_layout_container = QtWidgets.QWidget()
    grid_layout_container.setLayout(grid_layout)
    CORE.Object.attribute_content_area.setWidget(grid_layout_container)
    CORE.Object.attribute_content_area.setWidgetResizable(True)

    if target_attribute:
        for prop, option in target_attribute.items():
            selected_options[prop] = option
        for row in range(len(selected_options)):
            category_label = None
            property_combo = None
            if grid_layout.itemAtPosition(row, 0):
                category_label = grid_layout.itemAtPosition(row, 0).widget()
            if grid_layout.itemAtPosition(row, 1):
                property_combo = grid_layout.itemAtPosition(row, 1).widget()
            if category_label is not None and property_combo is not None:
                category = category_label.text()
                if category in selected_options:
                    selected_option = selected_options[category]
                    index = property_combo.findText(selected_option)
                    if index >= 0:
                        property_combo.setCurrentIndex(index)
    else:
        target_shape.attributes = selected_options
        CORE.Object.canvas.shapes[i] = target_shape
        save_attributes(CORE.Object.canvas.shapes)


def save_attributes(_shapes):
    filename = os.path.splitext(CORE.Variable.image_path)[0] + ".json"
    if CORE.Variable.output_dir:
        label_file_without_path = os.path.basename(filename)
        filename = os.path.join(CORE.Variable.output_dir, label_file_without_path)
    label_file = LabelFile()

    def format_shape(s):
        data = s.other_data.copy()
        info = {
            "label": s.label,
            "points": [(p.x(), p.y()) for p in s.points],
            "group_id": s.group_id,
            "description": s.description,
            "is_difficult": s.is_difficult,
            "shape_type": s.shape_type.name if isinstance(s.shape_type, ShapeType) else s.shape_type,
            "flags": s.flags,
            "attributes": s.attributes,
            "kie_linking": s.kie_linking,
        }
        if ShapeType.ROTATION == s.shape_type:
            info["direction"] = s.direction
        data.update(info)

        return data

    # Get current shapes
    # Excluding auto labeling special shapes
    shapes = [
        format_shape(shape)
        for shape in _shapes
        if shape.label not in (AutoLabelEditMode.OBJECT.name, AutoLabelEditMode.ADD.name, AutoLabelEditMode.REMOVE.name)
    ]
    flags = {}
    for i in range(CORE.Object.flag_widget.count()):
        item = CORE.Object.flag_widget.item(i)
        key = item.text()
        flag = item.checkState() == Qt.Checked
        flags[key] = flag
    try:
        if os.path.dirname(filename) and not os.path.exists(os.path.dirname(filename)):
            os.makedirs(os.path.dirname(filename))
        label_file.save(
            filename=filename,
            shapes=shapes,
            image_path=os.path.relpath(CORE.Variable.image_path, os.path.dirname(filename)),
            image_data=CORE.Variable.image_data if CORE.Variable.settings.get("store_data", False) else None,
            image_height=CORE.Variable.image.height(),
            image_width=CORE.Variable.image.width(),
            other_data=CORE.Variable.other_data,
            flags=flags,
        )
        CORE.Variable.label_file = label_file
        items = CORE.Object.info_file_list_widget.findItems(CORE.Variable.image_path, Qt.MatchExactly)
        if len(items) > 0:
            if len(items) != 1:
                raise RuntimeError("There are duplicate files.")
            items[0].setCheckState(Qt.Checked)
        return True
    except LabelFileError as e:
        show_critical_message("Error saving label data", f"<b>{e}</b>")
        return False


def reset_attribute(text):
    valid_labels = list(CORE.Variable.attributes.keys())
    if text not in valid_labels:
        most_similar_label = find_most_similar_label(text, valid_labels)
        show_critical_message("Invalid label", f"<p><b>Invalid label '{text}' with validation type: {valid_labels}!\nReset the label as {most_similar_label}.</b></p>", trace=False)
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
    CORE.Object.object_detection_button.setEnabled(value)
    CORE.Object.segmentation_button.setEnabled(value)
    CORE.Object.nlp_button.setEnabled(value)


def launch_async_job(target, args, callback):
    CORE.Variable.async_job_pool.add_job(target, args, callback)


def show_critical_message(title, content, trace=True):
    QtWidgets.QMessageBox.critical(
        CORE.Object.main_window,
        title,
        f"{content}\n{'Please see logs for detail.' if trace else ''}",
        QtWidgets.QMessageBox.Ok
    )
    if trace:
        logger.error(traceback.format_exc())
