import math
import os

from PyQt5.QtCore import QPointF, Qt

from core.configs.core import CORE
from core.dto.enums import ZoomMode


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


def add_zoom_value(increment):
    new_zoom_value = CORE.Object.zoom_widget.value() * increment
    if increment > 1:
        new_zoom_value = math.ceil(new_zoom_value)
    else:
        new_zoom_value = math.floor(new_zoom_value)
    set_zoom_value(new_zoom_value)


def set_zoom_value(value):
    # CORE.Action.fit_width.setChecked(False)
    # CORE.Action.fit_window.setChecked(False)
    CORE.Object.zoom_widget.setValue(value)
    CORE.Object.canvas.zoom_mode = ZoomMode.MANUAL_ZOOM
    CORE.Object.canvas.zoom_history[CORE.Variable.current_file_full_path] = (CORE.Object.canvas.zoom_mode, value)


def handle_scroll_request(delta, orientation):
    units = -delta * 0.1  # natural scroll
    scroll_bar = CORE.Object.canvas.scroll_bars[orientation]
    value = scroll_bar.value() + scroll_bar.singleStep() * units
    set_scroll_value(orientation, value)


def set_scroll_value(orientation, value):
    CORE.Object.canvas.scroll_bars[orientation].setValue(round(value))
    CORE.Object.canvas.scroll_values[orientation][CORE.Variable.current_file_full_path] = value


def handle_new_shape():
    """Pop-up and give focus to the label editor.

    position MUST be in global coordinates.
    """
    print("new shape")
    # items = self.unique_label_list.selectedItems()
    # text = None
    # if items:
    #     text = items[0].data(Qt.UserRole)
    # flags = {}
    # group_id = None
    # description = ""
    # difficult = False
    # kie_linking = []
    #
    # if self.canvas.shapes[-1].label in [
    #     AutoLabelingMode.ADD,
    #     AutoLabelingMode.REMOVE,
    # ]:
    #     text = self.canvas.shapes[-1].label
    # elif (
    #         self._config["display_label_popup"]
    #         or not text
    #         or self.canvas.shapes[-1].label == AutoLabelingMode.OBJECT
    # ):
    #     last_label = self.find_last_label()
    #     if self._config["auto_use_last_label"] and last_label:
    #         text = last_label
    #     else:
    #         previous_text = self.label_dialog.edit.text()
    #         (
    #             text,
    #             flags,
    #             group_id,
    #             description,
    #             difficult,
    #             kie_linking,
    #         ) = self.label_dialog.pop_up(text)
    #         if not text:
    #             self.label_dialog.edit.setText(previous_text)
    #
    # if text and not self.validate_label(text):
    #     self.error_message(
    #         self.tr("Invalid label"),
    #         self.tr("Invalid label '{}' with validation type '{}'").format(
    #             text, self._config["validate_label"]
    #         ),
    #     )
    #     text = ""
    #     return
    #
    # if self.attributes and text:
    #     text = self.reset_attribute(text)
    #
    # if text:
    #     self.label_list.clearSelection()
    #     shape = self.canvas.set_last_label(text, flags)
    #     shape.group_id = group_id
    #     shape.description = description
    #     shape.label = text
    #     shape.difficult = difficult
    #     shape.kie_linking = kie_linking
    #     self.add_label(shape)
    #     CORE.Action.edit_mode.setEnabled(True)
    #     CORE.Action.undo_last_point.setEnabled(False)
    #     CORE.Action.undo.setEnabled(True)
    #     self.set_dirty()
    # else:
    #     self.canvas.undo_last_line()
    #     self.canvas.shapes_backups.pop()


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
            CORE.Object.status_bar.showMessage(
                f"X: {int(pos.x())}, Y: {int(pos.y())} | H: {shape_height}, W: {shape_width} [{basename}: {current_index}/{num_images}]"
            )
        else:
            CORE.Object.status_bar.showMessage(
                f"X: {int(pos.x())}, Y: {int(pos.y())} | H: {shape_height}, W: {shape_width}"
            )
    elif CORE.Variable.label_file.image_path:
        if num_images and CORE.Variable.current_file_full_path in CORE.Variable.image_list:
            current_index = CORE.Variable.image_list.index(CORE.Variable.current_file_full_path) + 1
            CORE.Object.status_bar.showMessage(
                f"X: {int(pos.x())}, Y: {int(pos.y())} [{basename}: {current_index}/{num_images}]"
            )
        else:
            CORE.Object.status_bar.showMessage(f"X: {int(pos.x())}, Y: {int(pos.y())}")


def handle_selection_changed():
    print("selection changed")





def get_mode():
    return "Editing"

# def load_labels(shapes):
#     s = []
#     for shape in shapes:
#         label = shape["label"]
#         score = shape.get("score", None)
#         points = shape["points"]
#         shape_type = shape["shape_type"]
#         flags = shape["flags"]
#         group_id = shape["group_id"]
#         description = shape.get("description", "")
#         difficult = shape.get("difficult", False)
#         attributes = shape.get("attributes", {})
#         direction = shape.get("direction", 0)
#         kie_linking = shape.get("kie_linking", [])
#         other_data = shape["other_data"]
#
#         if label in self.hidden_cls or not points:
#             # skip point-empty shape
#             continue
#
#         shape = Shape(
#             label=label,
#             score=score,
#             shape_type=shape_type,
#             group_id=group_id,
#             description=description,
#             difficult=difficult,
#             direction=direction,
#             attributes=attributes,
#             kie_linking=kie_linking,
#         )
#         for x, y in points:
#             shape.add_point(QtCore.QPointF(x, y))
#         shape.close()
#
#         default_flags = {}
#         if self.label_flags:
#             for pattern, keys in self.label_flags.items():
#                 if re.match(pattern, label):
#                     for key in keys:
#                         default_flags[key] = False
#         shape.flags = default_flags
#         if flags:
#             shape.flags.update(flags)
#         shape.other_data = other_data
#
#         s.append(shape)
#     self.update_combo_box()
#     self.load_shapes(s)
