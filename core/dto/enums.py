from enum import Enum, unique


@unique
class ZoomMode(Enum):
    FIT_WINDOW = 0
    FIT_WIDTH = 1
    MANUAL_ZOOM = 2
