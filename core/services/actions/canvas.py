import math

from core.configs.core import CORE
from core.dto.enums import ZoomMode
from utils.logger import logger


def paint_canvas():
    if CORE.Variable.image.isNull():
        logger.error("cannot paint null image")
        return
    # CORE.Object.canvas.scale = 0.01 * self.zoom_widget.value()
    CORE.Object.canvas.adjustSize()
    CORE.Object.canvas.update()


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


def set_scroll_value(orientation, value):
    CORE.Object.canvas.scroll_bars[orientation].setValue(round(value))
    CORE.Object.canvas.scroll_values[orientation][CORE.Variable.current_file_full_path] = value
