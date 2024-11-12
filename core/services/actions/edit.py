import html
from typing import List

from PyQt5 import QtGui, QtWidgets
from PyQt5.QtCore import Qt

from core.configs.core import CORE
from core.dto.enums import CanvasMode, AutoLabelEditMode
from core.dto.label_list_widget_item import LabelListWidgetItem
from core.dto.shape import Shape
from core.services import system
from utils.function import get_rgb_by_label


def edit_label(item: 'LabelListWidgetItem'):
    if CORE.Object.canvas.canvas_mode != CanvasMode.EDIT:
        return
    if not item:
        items = CORE.Object.label_list_widget.selected_items()
        item = items[0] if items else None
    if item is None:
        return
    shape = item.shape()
    if shape is None:
        return
    text, flags, group_id, description, is_difficult, kie_linking = CORE.Object.label_dialog.pop_up(
        text=shape.label,
        flags=shape.flags,
        group_id=shape.group_id,
        description=shape.description,
        is_difficult=shape.is_difficult,
        kie_linking=shape.kie_linking
    )
    if text is None:
        return
    if CORE.Variable.attributes and text:
        text = system.reset_attribute(text)
    shape.label = text
    shape.flags = flags
    shape.group_id = group_id
    shape.description = description
    shape.is_difficult = is_difficult
    shape.kie_linking = kie_linking

    # Add to label history
    CORE.Object.label_dialog.add_label_history(shape.label)

    # Update unique label list
    if not CORE.Object.unique_label_list_widget.find_items_by_label(shape.label):
        unique_label_item = CORE.Object.unique_label_list_widget.create_item_from_label(shape.label)
        CORE.Object.unique_label_list_widget.addItem(unique_label_item)
        rgb = get_rgb_by_label(shape.label)
        CORE.Object.unique_label_list_widget.set_item_label(unique_label_item, shape.label, rgb, 128)

    Shape.update_shape_color(shape)
    if shape.group_id is None:
        color = shape.fill_color.getRgb()[:3]
        item.setText("{}".format(html.escape(shape.label)))
        item.setBackground(QtGui.QColor(*color, 128))
    else:
        item.setText(f"{shape.label} ({shape.group_id})")
    system.set_dirty()
    system.update_combo_box()


def add_label(shape: Shape):
    if shape.group_id is None:
        text = shape.label
    else:
        text = f"{shape.label} ({shape.group_id})"
    label_list_item = LabelListWidgetItem(text, shape)
    CORE.Object.label_list_widget.add_item(label_list_item)
    if not CORE.Object.unique_label_list_widget.find_items_by_label(shape.label):
        item = CORE.Object.unique_label_list_widget.create_item_from_label(shape.label)
        CORE.Object.unique_label_list_widget.addItem(item)
        rgb = get_rgb_by_label(shape.label)
        CORE.Object.unique_label_list_widget.set_item_label(item, shape.label, rgb, 128)

    # Add label to history if it is not a special label
    if shape.label not in (AutoLabelEditMode.OBJECT.value, AutoLabelEditMode.ADD.value, AutoLabelEditMode.REMOVE.value):
        CORE.Object.label_dialog.add_label_history(shape.label)

    CORE.Action.save_as.setEnabled(True)

    Shape.update_shape_color(shape)
    color = shape.fill_color.getRgb()[:3]
    label_list_item.setText("{}".format(html.escape(text)))
    label_list_item.setBackground(QtGui.QColor(*color, 128))
    system.update_combo_box()


def duplicate_selected_shape():
    added_shapes = CORE.Object.canvas.duplicate_selected_shapes()
    CORE.Object.label_list_widget.clearSelection()
    for shape in added_shapes:
        add_label(shape)
    system.set_dirty()


def delete_selected_shape():
    remove_labels(CORE.Object.canvas.delete_selected_shapes())
    system.set_dirty()
    if CORE.Object.canvas.is_no_shape:
        CORE.Action.save_as.setEnabled(False)


def remove_labels(shapes: List[Shape]):
    for shape in shapes:
        item = CORE.Object.label_list_widget.find_item_by_shape(shape)
        CORE.Object.label_list_widget.remove_item(item)
    system.update_combo_box()


def paste_selected_shape():
    system.load_shapes(CORE.Variable.copied_shapes, replace=False)
    system.set_dirty()


def copy_selected_shape():
    CORE.Variable.copied_shapes = [s.copy() for s in CORE.Object.canvas.selected_shapes]
    CORE.Action.paste_object.setEnabled(len(CORE.Variable.copied_shapes) > 0)


def remove_selected_point():
    CORE.Object.canvas.remove_selected_point()
    CORE.Object.canvas.update()
    if not CORE.Object.canvas.highlight_shape.points:
        CORE.Object.canvas.delete_shape(CORE.Object.canvas.highlight_shape)
        remove_labels([CORE.Object.canvas.highlight_shape])
        system.set_dirty()
        if CORE.Object.canvas.is_no_shape:
            CORE.Action.save_as.setEnabled(False)


def undo_shape_edit():
    CORE.Object.canvas.restore_shape()
    CORE.Object.label_list_widget.clear()
    system.load_shapes(CORE.Object.canvas.shapes)
    CORE.Action.undo.setEnabled(CORE.Object.canvas.is_shape_restorable)


def toggle_shapes_visibility(value):
    for item in CORE.Object.label_list_widget:
        item.setCheckState(Qt.Checked if value else Qt.Unchecked)
    CORE.Variable.settings.set("show_shapes", value)


def union_selection():
    """
    Merges selected shapes into one shape.
    """
    if len(CORE.Object.canvas.selected_shapes) < 2:
        QtWidgets.QMessageBox.warning(
            CORE.Object.main_window,
            "Warning",
            "Please select at least two shapes to perform union.",
            QtWidgets.QMessageBox.Ok,
        )
        return

    # Get rectangle of all selected shapes
    rectangle_shapes = []
    for shape in CORE.Object.canvas.selected_shapes:
        points = shape.points
        # Convert QPointF objects to tuples
        x_min, y_min = (points[0].x(), points[0].y())
        x_max, y_max = (points[2].x(), points[2].y())
        rectangle_shapes.append([x_min, y_min, x_max, y_max])

    # Calculate the rectangle
    min_x = min([bbox[0] for bbox in rectangle_shapes])
    min_y = min([bbox[1] for bbox in rectangle_shapes])
    max_x = max([bbox[2] for bbox in rectangle_shapes])
    max_y = max([bbox[3] for bbox in rectangle_shapes])

    # Create a new rectangle shape representing the union
    union_shape = CORE.Object.canvas.selected_shapes[-1].copy()
    union_shape.points[0].setX(min_x)
    union_shape.points[0].setY(min_y)
    union_shape.points[1].setX(max_x)
    union_shape.points[1].setY(min_y)
    union_shape.points[2].setX(max_x)
    union_shape.points[2].setY(max_y)
    union_shape.points[3].setX(min_x)
    union_shape.points[3].setY(max_y)
    add_label(union_shape)

    # clear selected shapes
    remove_labels(CORE.Object.canvas.delete_selected_shapes())
    system.set_dirty()

    # Update UI state
    if CORE.Object.canvas.is_no_shape:
        CORE.Action.save_as.setEnabled(False)


def copy_shape():
    CORE.Object.canvas.end_move(copy=True)
    for shape in CORE.Object.canvas.selected_shapes:
        add_label(shape)
    CORE.Object.label_list_widget.clearSelection()
    system.set_dirty()


def move_shape():
    CORE.Object.canvas.end_move(copy=False)
    system.set_dirty()
