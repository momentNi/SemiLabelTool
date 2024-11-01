import math
from typing import List, Tuple, Optional

import numpy as np
from PyQt5 import QtCore


def distance(p1: QtCore.QPointF, p2: QtCore.QPointF) -> float:
    """计算两点间欧式距离

    Args:
        p1: 点坐标
        p2: 点坐标

    Returns:
        欧氏距离
    """
    return math.sqrt((p1.x() - p2.x()) ** 2 + (p1.y() - p2.y()) ** 2)


def distance_to_line(point: QtCore.QPointF, line: tuple[QtCore.QPointF, QtCore.QPointF]) -> float:
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


def get_cross_point_of_two_lines(k1: float, b1: float, k2: float, b2: float) -> QtCore.QPointF | None:
    """
    Calculate the cross point of two lines with point-slope form.

    Args:
        k1: the slope of line1.
        b1: the intercept of line1.
        k2: the slope of line2.
        b2: the intercept of line2.

    Returns:
        QtCore.QPointF | None: The cross point of two lines, or None if these two lines are parallel.
    """
    if k1 == k2:
        return None
    x = (b2 - b1) / (k1 - k2)
    y = (k1 * b2 - k2 * b1) / (k1 - k2)
    return QtCore.QPointF(x, y)


def get_adjacent_points(theta: float, p3: QtCore.QPointF, p1: QtCore.QPointF, vertex_index: int) -> Tuple:
    """
    Get adjacent points of a `ShapeType.ROTATION`

    The bounded box of a rotation shape is a rectangle, which has a starting point P1.
    Returns the other 3 points of this rotation.
    (D)p4 ________________________ (C)p3
            ---------------------
            ----- rotation ------
            ------ theta --------
            ---------------------
    (A)p1 ________________________ (B)p2

    Args:
        theta (float): The rotation degree of rotation shape.
        p3 (QtCore.QPointF): The opposite corner point of p1.
        p1 (QtCore.QPointF): Reference point of rotation shape.
        vertex_index (int): The index of current operating vertex.

    Returns:
        p2, p3, p4 (QtCore.QPointF): Three points that describe a part of the shape related to the given angle.
    """
    # the tangent of rotation degree
    k1 = math.tan(theta)

    if k1 == 0:
        # rotation for special degree, theta = k * pi (k = 0, 1, 2, ...)
        if vertex_index % 2 == 0:
            # Operation on the bottom-left or top-right vertex
            p2 = QtCore.QPointF(p3.x(), p1.y())
            p4 = QtCore.QPointF(p1.x(), p3.y())
        else:
            # Operation on the bottom-right or top-left vertex, mirror p2 and p4
            p4 = QtCore.QPointF(p3.x(), p1.y())
            p2 = QtCore.QPointF(p1.x(), p3.y())
    else:
        # rotation for common degree
        # AB // CD
        k3 = k1
        # AB ⊥ BC, AD ⊥ DC, slope1 * slope2 = -1
        k2 = -1 / k1
        k4 = -1 / k1
        # the intercept of line AB
        b1 = p1.y() - k1 * p1.x()
        # the intercept of line BC
        b2 = p1.y() - k2 * p1.x()
        # the intercept of line CD
        b3 = p3.y() - k1 * p3.x()
        # the intercept of line AD
        b4 = p3.y() - k2 * p3.x()

        if vertex_index % 2 == 0:
            p2 = get_cross_point_of_two_lines(k1, b1, k4, b4)
            p4 = get_cross_point_of_two_lines(k2, b2, k3, b3)
        else:
            p4 = get_cross_point_of_two_lines(k1, b1, k4, b4)
            p2 = get_cross_point_of_two_lines(k2, b2, k3, b3)

    return p2, p3, p4


def intersection_point_with_box(p1: QtCore.QPointF, p2: QtCore.QPointF, width: int, height: int) -> QtCore.QPointF:
    """Cycle through each image edge in clockwise fashion,
    and find the one intersecting the current line segment.
    """
    box_points = [
        (0, 0),
        (width - 1, 0),
        (width - 1, height - 1),
        (0, height - 1),
    ]
    # x1, y1 should be in the pixmap, x2, y2 should be out of the pixmap
    x1 = min(max(p1.x(), 0), width - 1)
    y1 = min(max(p1.y(), 0), height - 1)
    x2, y2 = p2.x(), p2.y()
    _, i, (x, y) = min(intersecting_edges_with_box((x1, y1), (x2, y2), box_points))
    x3, y3 = box_points[i]
    x4, y4 = box_points[(i + 1) % 4]
    x1, y1 = int(x1), int(y1)
    x2, y2 = int(x2), int(y2)
    x3, y3 = int(x3), int(y3)
    x4, y4 = int(x4), int(y4)
    if (x, y) == (x1, y1):
        # Handle cases where previous point is on one of the edges.
        if x3 == x4:
            return QtCore.QPointF(x3, min(max(0, y2), max(y3, y4)))
        # y3 == y4
        return QtCore.QPointF(min(max(0, x2), max(x3, x4)), y3)
    return QtCore.QPointF(int(x), int(y))


def intersecting_edges_with_box(point1: Tuple[float, float], point2: Tuple[float, float], box_points: List[Tuple[float, float]]) -> Tuple:
    """
    Find the intersecting edges with box using yield.

    Line1(Target Line): direction vector ^u = point1 - point2 = (x2 - x1, y2 - y1)
    Line2(Box Edge): direction vector ^v = points[(i + 1) % 4] - points[i] = (x4 - x3, y4 - y3)

    So, these two line can be presented like below:
    Line1: x = x1 + t(x2 - x1)     Line2: x = x3 + s(x4 - x3)
           y = y1 + t(y2 - y1)            y = y3 + s(y4 - y3)

    Combine:
           x1 + t(x2 - x1) = x3 + s(x4 - x3) ===> (x2 - x1)t - (x4 - x3)s = x3 - x1
           y1 + t(y2 - y1) = y3 + s(y4 - y3) ===> (y2 - y1)t - (y4 - y3)s = y3 - y1

    Determinant D = (x2 - x1)(y4 - y3) - (y2 - y1)(x4 - x3)
        if D == 0, these two lines are either parallel or coincident, and there is no single intersection.
        if D != 0, these two lines have a unique solution for t and s
            t = ((x4 - x3)(y3 - y1) - (y4 - y3)(x3 - x1)) / D
            s = ((x2 - x1)(y3 - y1) - (y2 - y1)(x3 - x1)) / D

    Args:
        point1: start point of target line
        point2: end point of target line
        box_points: the four points of box in clockwise sequence

    Returns:
        float: The distance between the middle point of the current edge and the end point of direction.
        int: The index of edge intersecting with target line.
        Tuple[float, float]: The intersection point
    """
    (x1, y1) = point1
    (x2, y2) = point2
    for i in range(4):
        x3, y3 = box_points[i]
        x4, y4 = box_points[(i + 1) % 4]
        det = (y4 - y3) * (x2 - x1) - (x4 - x3) * (y2 - y1)
        det_t = (x4 - x3) * (y3 - y1) - (y4 - y3) * (x3 - x1)
        det_s = (x2 - x1) * (y3 - y1) - (y2 - y1) * (x3 - x1)
        if det == 0:
            # det_t == det_s == 0: Coincident
            # otherwise: Parallel
            continue
        t, s = det_t / det, det_s / det
        # Validation
        if 0 <= t <= 1 and 0 <= s <= 1:
            # The line segments intersect, and the intersection point lies within both segments
            # Calculate the intersection point
            x = x1 + t * (x2 - x1)
            y = y1 + t * (y2 - y1)
            # Calculate the middle point of the current edge
            middle_edge_point = QtCore.QPointF((x3 + x4) / 2, (y3 + y4) / 2)
            # Calculate the distance between the middle point of the current edge and the end point of direction,
            # So that the one closest can be chosen.
            d = distance(middle_edge_point, QtCore.QPointF(x2, y2))
            yield d, i, (x, y)
        else:
            # Otherwise, the lines intersect but not within the segments.
            continue


def rotate_point(p: QtCore.QPointF, center: QtCore.QPointF, theta: float) -> QtCore.QPointF:
    """
    Rotate a point around a given center by a specified angle.

    Args:
        p (QtCore.QPointF): The point to be rotated.
        center (QtCore.QPointF): The center of rotation.
        theta (float): The rotation angle in radians.

    Returns:
        QtCore.QPointF: The new position of the point after rotation.
    """
    # direction vector
    order = p - center
    cos_theta = math.cos(theta)
    sin_theta = math.sin(theta)
    new_x = cos_theta * order.x() + sin_theta * order.y()
    new_y = -sin_theta * order.x() + cos_theta * order.y()
    return QtCore.QPointF(center.x() + new_x, center.y() + new_y)


def rectangle_from_diagonal(diagonal_vertices: List[List[int]]) -> List[List[int]]:
    """Generate rectangle vertices from diagonal vertices.

    Args:
        diagonal_vertices: List containing two points representing the diagonal vertices.

    Returns:
        List containing four points representing the rectangle's four corners.
        [top-left, top-right, bottom-right, bottom-left]
    """
    x1, y1 = diagonal_vertices[0]
    x2, y2 = diagonal_vertices[1]

    return [
        [x1, y1],
        [x2, y1],
        [x2, y2],
        [x1, y2],
    ]


def get_rect_from_line(p1: QtCore.QPointF, p2: QtCore.QPointF) -> QtCore.QRectF:
    """Get rectangle from diagonal line
    
    Args:
        p1: Point1 on the line
        p2: Point1 on the line

    Returns:
        QRectF Object of rectangle
    """
    x1, y1 = p1.x(), p1.y()
    x2, y2 = p2.x(), p2.y()
    return QtCore.QRectF(x1, y1, x2 - x1, y2 - y1)


def get_circle_rect_from_line(line: List[QtCore.QPointF]) -> Optional[QtCore.QRectF]:
    if len(line) != 2:
        return None
    (c, _) = line
    r = line[0] - line[1]
    d = math.sqrt(r.x() ** 2 + r.y() ** 2)
    return QtCore.QRectF(c.x() - d, c.y() - d, 2 * d, 2 * d)
