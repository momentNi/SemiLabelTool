import logging

import imgviz
from PyQt5 import QtGui

from core.dto.enums import Device


class Constants:
    APP_NAME: str = 'SemiLabelTool'
    APP_DESCRIPTION: str = 'Advanced Auto Labeling Solution with Added Features'
    APP_VERSION: str = '0.1.0'

    DEVICE = Device.CPU  # GPU or CPU

    LABEL_OPACITY = 128
    LABEL_COLOR_MAP = imgviz.label_colormap()
    DEFAULT_LINE_COLOR = QtGui.QColor(0, 255, 0, 128)
    DEFAULT_FILL_COLOR = QtGui.QColor(100, 100, 100, 100)
    DEFAULT_SELECT_LINE_COLOR = QtGui.QColor(255, 255, 255)
    DEFAULT_SELECT_FILL_COLOR = QtGui.QColor(0, 255, 0, 155)
    DEFAULT_VERTEX_FILL_COLOR = QtGui.QColor(0, 255, 0, 255)
    DEFAULT_HIGHLIGHT_VERTEX_FILL_COLOR = QtGui.QColor(255, 255, 255, 255)

    FORMAT = "$asctime - $levelname - $filename[line:$lineno]: $message"
    COLORS = {
        logging.DEBUG: "\x1b[;11m",  # GREY
        logging.INFO: "\x1b[32;11m",  # GREEN
        logging.WARNING: "\x1b[33;11m",  # YELLOW
        logging.ERROR: "\x1b[31;11m",  # RED
        logging.CRITICAL: "\x1b[41;1m"  # BOLD RED
    }
