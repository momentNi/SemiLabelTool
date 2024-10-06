from enum import Enum, unique


@unique
class ZoomMode(Enum):
    FIT_WINDOW = 0
    FIT_WIDTH = 1
    MANUAL_ZOOM = 2


@unique
class PointType(Enum):
    SQUARE = 0
    ROUND = 1


@unique
class ShapeType(Enum):
    POINT = 1
    RECTANGLE = 2
    POLYGON = 3
    CIRCLE = 4
    LINE = 5
    ROTATION = 6
    LINE_STRIP = 7


@unique
class CanvasMode(Enum):
    CREATE = 1
    EDIT = 2


@unique
class AutoLabelEditMode(Enum):
    OFF = 0
    ADD = 1
    REMOVE = 2


@unique
class AutoLabelShapeType(Enum):
    OFF = 0
    POINT = 1
    RECTANGLE = 2


@unique
class ShapeHighlightMode(Enum):
    # Flag for the handles we would move if dragging
    MOVE_VERTEX = (4, PointType.ROUND)
    # Flag for all other handles on the current shape
    NEAR_VERTEX = (1.5, PointType.SQUARE)
