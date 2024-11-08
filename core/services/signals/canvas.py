import os

from PyQt5.QtCore import QPointF, Qt

from core.configs.core import CORE
from core.dto.enums import AutoLabelEditMode, ShapeType
from core.services import system
from core.services.actions.canvas import add_zoom_value, set_scroll_value
from core.services.actions.edit import add_label
from core.services.system import find_last_label, update_attributes


def handle_zoom_request(delta: float, pos: QPointF):
    old_width = CORE.Object.canvas.width()
    units = 0.9 if delta < 0 else 1.1
    add_zoom_value(units)

    new_width = CORE.Object.canvas.width()
    if old_width != new_width:
        canvas_scale_factor = new_width / old_width
        x_shift = round(pos.x() * canvas_scale_factor - pos.x())
        y_shift = round(pos.y() * canvas_scale_factor - pos.y())
        set_scroll_value(Qt.Horizontal, CORE.Object.canvas.scroll_bars[Qt.Horizontal].value() + x_shift)
        set_scroll_value(Qt.Vertical, CORE.Object.canvas.scroll_bars[Qt.Vertical].value() + y_shift)


def handle_scroll_request(delta, orientation):
    units = -delta * 0.1
    scroll_bar = CORE.Object.canvas.scroll_bars[orientation]
    value = scroll_bar.value() + scroll_bar.singleStep() * units
    set_scroll_value(orientation, value)


def handle_new_shape():
    items = CORE.Object.unique_label_list_widget.selectedItems()
    text = None
    if items:
        text = items[0].data(Qt.UserRole)
    flags = {}
    group_id = None
    description = ""
    is_difficult = False
    kie_linking = []

    if CORE.Object.canvas.shapes[-1].label in (AutoLabelEditMode.ADD.value, AutoLabelEditMode.REMOVE.value):
        text = CORE.Object.canvas.shapes[-1].label
    elif not text or CORE.Object.canvas.shapes[-1].label == AutoLabelEditMode.OBJECT.value:
        last_label = find_last_label()
        if CORE.Variable.settings.get("auto_use_last_label", False) and last_label:
            text = last_label
        else:
            previous_text = CORE.Object.label_dialog.line_edit.text()
            text, flags, group_id, description, is_difficult, kie_linking = CORE.Object.label_dialog.pop_up(text)
            if not text:
                CORE.Object.label_dialog.line_edit.setText(previous_text)

    if CORE.Variable.attributes and text:
        text = system.reset_attribute(text)

    if text:
        CORE.Object.label_list_widget.clearSelection()
        shape = CORE.Object.canvas.set_last_label(text, flags)
        shape.group_id = group_id
        shape.description = description
        shape.label = text
        shape.is_difficult = is_difficult
        shape.kie_linking = kie_linking
        add_label(shape)
        CORE.Action.edit_object.setEnabled(True)
        CORE.Action.undo_last_point.setEnabled(False)
        CORE.Action.undo.setEnabled(True)
        system.set_dirty()
    else:
        CORE.Object.canvas.undo_last_line()
        CORE.Object.canvas.shapes_backups.pop()


def handle_show_shape(shape_height: float, shape_width: float, pos: QPointF):
    """Display annotation width and height while hovering inside.

    Parameters:
    - shape_height (float): The height of the shape.
    - shape_width (float): The width of the shape.
    - pos (QPointF): The current mouse coordinates inside the shape.
    """
    num_images = len(CORE.Variable.image_list)
    basename = os.path.basename(str(CORE.Variable.current_file_full_path))
    if shape_height > 0 and shape_width > 0:
        if num_images and CORE.Variable.current_file_full_path in CORE.Variable.image_list:
            current_index = CORE.Variable.image_list.index(CORE.Variable.current_file_full_path) + 1
            CORE.Object.status_bar.showMessage(f"X: {int(pos.x())}, Y: {int(pos.y())} | H: {shape_height}, W: {shape_width} [{basename}: {current_index}/{num_images}]")
        else:
            CORE.Object.status_bar.showMessage(f"X: {int(pos.x())}, Y: {int(pos.y())} | H: {shape_height}, W: {shape_width}")
    elif CORE.Variable.image_path:
        if num_images and CORE.Variable.current_file_full_path in CORE.Variable.image_list:
            current_index = CORE.Variable.image_list.index(CORE.Variable.current_file_full_path) + 1
            CORE.Object.status_bar.showMessage(f"X: {int(pos.x())}, Y: {int(pos.y())} [{basename}: {current_index}/{num_images}]")
        else:
            CORE.Object.status_bar.showMessage(f"X: {int(pos.x())}, Y: {int(pos.y())}")


def handle_selection_changed(selected_shapes):
    CORE.Variable.has_selection_slot = False
    for shape in CORE.Object.canvas.selected_shapes:
        shape.is_selected = False
    CORE.Object.label_list_widget.clearSelection()
    CORE.Object.canvas.selected_shapes = selected_shapes
    can_merge = True
    for shape in CORE.Object.canvas.selected_shapes:
        shape.is_selected = True
        if shape.shape_type != ShapeType.RECTANGLE:
            can_merge = False
        item = CORE.Object.label_list_widget.find_item_by_shape(shape)
        if item is not None:
            CORE.Object.label_list_widget.select_item(item)
            CORE.Object.label_list_widget.scroll_to_item(item)
    CORE.Variable.has_selection_slot = True
    n_selected = len(selected_shapes)
    CORE.Action.delete_polygon.setEnabled(n_selected)
    CORE.Action.duplicate_polygon.setEnabled(n_selected)
    CORE.Action.copy_object.setEnabled(n_selected)
    CORE.Action.edit_label.setEnabled(n_selected == 1)
    CORE.Action.union_selection.setEnabled(can_merge and n_selected > 1)
    system.set_item_description(True)
    if CORE.Variable.attributes:
        for i in range(len(CORE.Object.canvas.shapes)):
            if CORE.Object.canvas.shapes[i].is_selected:
                update_attributes(i)
                break
