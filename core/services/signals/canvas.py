import os

from PyQt5.QtCore import QPointF, Qt

from core.configs.core import CORE
from core.services.actions.canvas import add_zoom_value, set_scroll_value


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
    """Pop-up and give focus to the label editor.

    position MUST be in global coordinates.
    """
    print("new shape")


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
