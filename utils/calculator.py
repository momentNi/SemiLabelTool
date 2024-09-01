"""
计算类工具方法
"""
import math

import numpy as np
from PyQt5.QtCore import QPointF


def distance(p1: QPointF, p2: QPointF) -> float:
    """计算两点间欧式距离

    Args:
        p1: 点坐标
        p2: 点坐标

    Returns:
        欧氏距离
    """
    return math.sqrt((p1.x() - p2.x()) ** 2 + (p1.y() - p2.y()) ** 2)


def distance_to_line(point: QPointF, line: tuple[QPointF, QPointF]) -> float:
    """计算点到直线的距离

    Args:
        point:  点坐标
        line: 直线上任意两点

    Returns:
        float: 点到直线的距离
    """
    p1, p2 = line
    p1 = np.array([p1.x(), p1.y()])
    p2 = np.array([p2.x(), p2.y()])
    p3 = np.array([point.x(), point.y()])
    if np.dot((p3 - p1), (p2 - p1)) < 0:
        return np.linalg.norm(p3 - p1)
    if np.dot((p3 - p2), (p1 - p2)) < 0:
        return np.linalg.norm(p3 - p2)
    if np.linalg.norm(p2 - p1) == 0:
        return 0
    return np.linalg.norm(np.cross(p2 - p1, p1 - p3)) / np.linalg.norm(p2 - p1)
