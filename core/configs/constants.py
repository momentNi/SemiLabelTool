import imgviz
from PyQt5 import QtGui


class Constants:
    APP_NAME: str = 'SemiLabelTool'
    APP_DESCRIPTION: str = 'Advanced Auto Labeling Solution with Added Features'
    APP_VERSION: str = '0.1.0'

    DEVICE = "GPU"  # GPU or CPU

    LABEL_COLOR_MAP = imgviz.label_colormap()
    DEFAULT_LINE_COLOR = QtGui.QColor(0, 255, 0, 128)
    DEFAULT_FILL_COLOR = QtGui.QColor(100, 100, 100, 100)
    DEFAULT_SELECT_LINE_COLOR = QtGui.QColor(255, 255, 255)
    DEFAULT_SELECT_FILL_COLOR = QtGui.QColor(0, 255, 0, 155)
    DEFAULT_VERTEX_FILL_COLOR = QtGui.QColor(0, 255, 0, 255)
    DEFAULT_HOVER_VERTEX_FILL_COLOR = QtGui.QColor(255, 255, 255, 255)

    SHAPE_POINT_SIZE = 4
    SHAPE_SCALE = 1.5
    SHAPE_LINE_WIDTH = 2.0
