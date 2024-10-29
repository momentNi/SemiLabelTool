from enum import Enum, unique


@unique
class ZoomMode(Enum):
    """
    Canvas Zooming mode
    """
    FIT_WINDOW = 0
    FIT_WIDTH = 1
    MANUAL_ZOOM = 2


@unique
class PointType(Enum):
    """
    Point appearance type
    """
    # Square point
    SQUARE = 0
    # Round point
    ROUND = 1


@unique
class ShapeType(Enum):
    """
    Shape type to create new shapes
    """
    POINT = 1
    RECTANGLE = 2
    POLYGON = 3
    CIRCLE = 4
    LINE = 5
    ROTATION = 6
    LINE_STRIP = 7

    def __str__(self):
        return self.name


@unique
class CanvasMode(Enum):
    """
    Canvas Operating Mode
    """
    # Mode for drawing shapes
    CREATE = 1
    # Mode for editing shapes
    EDIT = 2


@unique
class AutoLabelEditMode(Enum):
    """
    Edit mode for Auto Labeling
    """
    # Not use auto labeling
    OFF = "OFF"
    # Object label added by auto label
    OBJECT = "AUTO_OBJECT"
    # Label added by auto label
    ADD = "AUTO_ADD"
    # Label removed by auto label
    REMOVE = "AUTO_REMOVE"


@unique
class AutoLabelShapeType(Enum):
    """
    Shape mode for Auto Labeling
    """
    # Not use auto labeling
    OFF = 0
    # Shape type is a point
    POINT = 1
    # Shape type is a rectangle
    RECTANGLE = 2


@unique
class ShapeHighlightMode(Enum):
    """
    Highlight mode for shape
    """
    # Flag for the handles we would move if dragging
    MOVE_VERTEX = (4, PointType.ROUND)
    # Flag for all other handles on the current shape
    NEAR_VERTEX = (1.5, PointType.SQUARE)
