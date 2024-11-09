import copy
from typing import List, Self, Optional

from PyQt5 import QtGui, QtCore

from core.configs.constants import Constants
from core.configs.core import CORE
from core.dto.enums import ShapeType, PointType, ShapeHighlightMode
from core.dto.exceptions import WrongShapeError
from utils.calculator import get_rect_from_line, get_circle_rect_from_line, distance, distance_to_line
from utils.function import get_rgb_by_label
from utils.logger import logger


class Shape:
    def __init__(self, label=None, score=None, line_color=None, shape_type=None, flags=None, group_id=None, description=None, is_difficult=False, direction=0, attributes=None, kie_linking=None):
        self.label: str = label
        self.cache_label: Optional[str] = None
        self.score: float = score
        self._shape_type: 'ShapeType' = shape_type if shape_type is not None else ShapeType.POLYGON
        self.flags: dict = flags
        self.group_id: int = group_id
        self.description: str = description
        self.is_difficult: bool = is_difficult
        self.direction: int = direction
        self.attributes: dict = attributes if attributes is not None else {}
        self.kie_linking: List[str] = kie_linking if kie_linking is not None else []
        self.other_data: dict = {}

        self.point_type: 'PointType' = PointType.ROUND
        self.point_size: float = 1.5
        self.line_width: float = 2.0
        self.points: List[QtCore.QPointF] = []
        self.center: Optional[QtCore.QPointF] = None

        self.highlight_vertex_index: Optional[int] = None
        self.highlight_mode: 'ShapeHighlightMode' = ShapeHighlightMode.NEAR_VERTEX

        # Color related
        self.line_color: QtGui.QColor = line_color if line_color is not None else Constants.DEFAULT_LINE_COLOR
        self.fill_color: QtGui.QColor = Constants.DEFAULT_FILL_COLOR
        self.select_line_color: QtGui.QColor = Constants.DEFAULT_SELECT_LINE_COLOR
        self.select_fill_color: QtGui.QColor = Constants.DEFAULT_SELECT_FILL_COLOR
        self.vertex_fill_color: QtGui.QColor = Constants.DEFAULT_VERTEX_FILL_COLOR
        self._vertex_fill_color: Optional[QtGui.QColor] = None
        self.highlight_vertex_fill_color: QtGui.QColor = Constants.DEFAULT_HIGHLIGHT_VERTEX_FILL_COLOR

        self.is_visible: bool = True
        self.is_fill: bool = False
        self.is_selected: bool = False
        self.is_closed: bool = False
        self.show_degrees: bool = True

    def __len__(self) -> int:
        return len(self.points)

    def __str__(self) -> str:
        return str(self.__dict__)

    def __getitem__(self, key: int) -> QtCore.QPointF:
        return self.points[key]

    def __setitem__(self, key: int, value: QtCore.QPointF) -> QtCore.QPointF:
        self.points[key] = value
        return value

    @property
    def shape_type(self):
        return self._shape_type

    @shape_type.setter
    def shape_type(self, value):
        try:
            self._shape_type = ShapeType(value)
        except ValueError:
            logger.error(f"Unexpected shape_type: {value}")
            raise ValueError(f"Unexpected shape_type: {value}")

    @staticmethod
    def update_shape_color(shape):
        r, g, b = get_rgb_by_label(shape.label)
        shape.line_color = QtGui.QColor(r, g, b)
        shape.vertex_fill_color = QtGui.QColor(r, g, b)
        shape.highlight_vertex_fill_color = QtGui.QColor(255, 255, 255)
        shape.fill_color = QtGui.QColor(r, g, b, 128)
        shape.select_line_color = QtGui.QColor(255, 255, 255)
        shape.select_fill_color = QtGui.QColor(r, g, b, 155)

    def copy(self) -> Self:
        return copy.deepcopy(self)

    def make_path(self) -> QtGui.QPainterPath:
        """
        Create a QPainterPath based on the shape type.

        This method generates a QPainterPath object depending on the shape type (rectangle, circle, or other polygon).
        For rectangles and circles, specific algorithms are used to create the path.
        For other polygons, it creates the path by iterating through the list of points.

        Returns:
            QPainterPath: The drawing path representing the shape.
        """
        if self._shape_type == ShapeType.RECTANGLE:
            path = QtGui.QPainterPath(self.points[0])
            for p in self.points[1:]:
                path.lineTo(p)
        elif self._shape_type == ShapeType.CIRCLE:
            path = QtGui.QPainterPath()
            if len(self.points) == 2:
                rectangle = get_circle_rect_from_line(self.points)
                path.addEllipse(rectangle)
        else:
            path = QtGui.QPainterPath(self.points[0])
            for p in self.points[1:]:
                path.lineTo(p)
        return path

    def close_shape(self) -> None:
        """
        Closes the current drawing shape.

        For rotation type shapes, if there are four points, calculate the center point and assign it to self.center.
        Mark the shape as closed.
        """
        if self._shape_type == ShapeType.ROTATION and len(self.points) == 4:
            cx = (self.points[0].x() + self.points[2].x()) / 2
            cy = (self.points[0].y() + self.points[2].y()) / 2
            self.center = QtCore.QPointF(cx, cy)
        self.is_closed = True

    def is_reach_max_points(self) -> bool:
        """
        Check whether the current shape has reached the maximum point amount.

        Returns:
            bool: True if the number of points in the current shape is greater than or equal to 4, otherwise False.
        """
        return len(self.points) >= 4

    def contains_point(self, point: QtCore.QPointF) -> bool:
        """
        Check if shape contains a point

        Args:
            point (QPointF): Target point

        Returns:
            Whether target point is inside shape
        """
        return self.make_path().contains(point)

    def can_add_point(self) -> bool:
        """
        Determines whether the current shape can add more points.

        This method checks if the current shape type allows adding more points. Only shapes of type
        POLYGON and LINE_STRIP can add more points.

        Returns:
            bool: A boolean value, returns True if the current shape can add more points, otherwise False.
        """
        return self._shape_type in (ShapeType.POLYGON, ShapeType.LINE_STRIP)

    def get_nearest_vertex(self, point: QtCore.QPointF, epsilon: float) -> int | None:
        """
        Find the nearest vertex to a given point from a collection of vertices.

        Parameters:
            point (QPointF): The coordinate point to find the nearest vertex to.
            epsilon (float): The maximum allowed distance between the nearest vertex and the given point.

        Returns:
            int | None: The index of the nearest vertex if the distance is within epsilon; otherwise, None.
        """
        min_distance = float("inf")
        min_i = None
        for i, p in enumerate(self.points):
            dist = distance(p, point)
            if dist <= epsilon and dist < min_distance:
                min_distance = dist
                min_i = i
        return min_i

    def get_nearest_edge(self, point: QtCore.QPointF, epsilon: float) -> int | None:
        """
        Get the index of the nearest edge to the given point.

        This method iterates through all pairs of points, calculates the distance from the given point to each edge,
        and returns the index of the nearest edge.
        If no edge is within the epsilon distance, it returns None.

        Parameters:
            point (QPointF): Coordinates of the given point.
            epsilon (float): Distance threshold to determine if a point is close to an edge.

        Returns:
            Index of the nearest edge (zero-based), or None if no edge is within the epsilon distance.
        """
        min_distance = float("inf")
        post_i = None
        for i in range(len(self.points)):
            dist = distance_to_line(point, (self.points[i - 1], self.points[i]))
            if dist <= epsilon and dist < min_distance:
                min_distance = dist
                post_i = i
        return post_i

    def get_bounding_rect(self) -> QtCore.QRectF:
        """
        Gets the bounding rectangle of the current object.

        This method calculates and returns the bounding rectangle of the current object.
        The rectangle is represented by a QRectF object.

        Returns:
            QRectF: The bounding rectangle of the current object.
        """
        return self.make_path().boundingRect()

    def add_point(self, point: QtCore.QPointF) -> None:
        """
        Add a new point to current shape.

        Args:
            point (QPointF): new point to be added
        """
        if self._shape_type == ShapeType.RECTANGLE:
            if not self.is_reach_max_points():
                self.points.append(point)
        else:
            if self.points and point == self.points[0]:
                self.close_shape()
            else:
                self.points.append(point)

    def insert_point(self, i: int, point: QtCore.QPointF) -> None:
        """
        Insert a new point into the current shape at a specified index.

        Args:
            i (int): The index at which to insert the new point.
            point (QPointF): The new point to insert.
        """
        self.points.insert(i, point)

    def pop_point(self) -> QtCore.QPointF | None:
        """
        Remove and return the last point of the shape.

        If the shape has any points, return the last point.
        Otherwise, return None.

        Returns:
            QPointF | None: The last point of the shape if it has any point. Otherwise, it returns None.
        """
        return self.points.pop() if self.points else None

    def remove_point(self, i: int) -> QtCore.QPointF | None:
        """
        Remove and return the point at the specified index.
        Returns None if the index is out of range.

        Parameters:
            i (int): The index of the point.

        Returns:
            QPointF | None: The removed point, or None if the index is out of range.
        """
        try:
            return self.points.pop(i)
        except IndexError:
            return None

    def move_point(self, i: int, offset: QtCore.QPointF) -> None:
        """
        Move the position of a specified point.

        This method modifies the position of the point at index i by adding the given offset.

        Parameters:
            i (int): The index of the point to be moved.
            offset (QPointF): The offset to apply to the point's position.
        """
        self.points[i] = self.points[i] + offset

    def move_shape(self, offset: QtCore.QPointF) -> None:
        """
        Move the shape to a new position.

        This method moves the shape by adding the given offset to each point in the current shape.

        Parameters:
            offset (QPointF): The offset to move by, representing the difference between the new and current positions.
        """
        self.points = [p + offset for p in self.points]

    def highlight_vertex(self, i, action: ShapeHighlightMode) -> None:
        """
        Highlights a vertex.

        This method sets the index of the vertex to be highlighted and the highlighting mode.

        Args:
            i (int): The index of the vertex to be highlighted.
            action (ShapeHighlightMode): The highlighting mode that defines how the vertex should be highlighted.
        """
        self.highlight_vertex_index = i
        self.highlight_mode = action

    def highlight_clear(self):
        """
        Clear the highlighted point
        """
        self.highlight_vertex_index = None

    def draw_vertex(self, path: QtGui.QPainterPath, i: int):
        """
        Draws a vertex shape.

        This method is responsible for adding a vertex shape to the given QPainterPath based on the selected point type.
        It adjusts the size and color of the point based on its position, whether it is highlighted, and highlight mode.

        Args:
            path (QtGui.QPainterPath): QPainterPath object used to draw the vertex shape.
            i (int): Index of the current vertex to draw, used to determine its position in the points list.

        Raises:
            WrongShapeError: If the vertex shape is unsupported.
        """
        d = self.point_size / CORE.Variable.shape_scale
        shape = self.point_type
        point = self.points[i]
        if i == self.highlight_vertex_index:
            size, shape = self.highlight_mode.value
            d *= size
        if self.highlight_vertex_index is not None:
            self._vertex_fill_color = self.highlight_vertex_fill_color
        else:
            self._vertex_fill_color = self.vertex_fill_color
        if shape == PointType.SQUARE:
            path.addRect(point.x() - d / 2, point.y() - d / 2, d, d)
        elif shape == PointType.ROUND:
            path.addEllipse(point, d / 2.0, d / 2.0)
        else:
            logger.error(f"Unsupported vertex shape: {shape}")
            raise WrongShapeError("Unsupported vertex shape")

    def paint(self, painter: QtGui.QPainter):
        """
        Draws the shape.

        This method is responsible for drawing the shape using the specified painter object.
        It draws lines, vertices, and fills based on the shape's type, selected state, and other properties.

        Args:
            painter (QtGui.QPainter): The painter object used for drawing.
        """
        if self.points:
            color = self.select_line_color if self.is_selected else self.line_color
            pen = QtGui.QPen(color)
            pen.setWidth(max(1, int(round(self.line_width / CORE.Variable.shape_scale))))
            painter.setPen(pen)

            line_path = QtGui.QPainterPath()
            vertex_path = QtGui.QPainterPath()

            if self.shape_type == ShapeType.RECTANGLE or self.shape_type == ShapeType.ROTATION:
                if len(self.points) not in (1, 2, 4):
                    logger.error(f"Invalid points length (points = {self.points}) for {self.shape_type}")
                    raise WrongShapeError(f"Invalid points length (points = {self.points}) for {self.shape_type}")
                if len(self.points) == 2:
                    rectangle = get_rect_from_line(*self.points)
                    line_path.addRect(rectangle)
                elif len(self.points) == 4:
                    line_path.moveTo(self.points[0])
                    for i, p in enumerate(self.points):
                        line_path.lineTo(p)
                        if self.is_selected:
                            self.draw_vertex(vertex_path, i)
                    if self.is_closed or self.label is not None:
                        line_path.lineTo(self.points[0])
            elif self._shape_type == ShapeType.CIRCLE:
                if len(self.points) not in [1, 2]:
                    logger.error(f"Invalid points length (points = {self.points}) for {self._shape_type}")
                    raise WrongShapeError(f"Invalid points length (points = {self.points}) for {self._shape_type}")
                if len(self.points) == 2:
                    rectangle = get_circle_rect_from_line(self.points)
                    line_path.addEllipse(rectangle)
                if self.is_selected:
                    for i in range(len(self.points)):
                        self.draw_vertex(vertex_path, i)
            elif self._shape_type == ShapeType.LINE_STRIP:
                line_path.moveTo(self.points[0])
                for i, p in enumerate(self.points):
                    line_path.lineTo(p)
                    if self.is_selected:
                        self.draw_vertex(vertex_path, i)
            elif self._shape_type == ShapeType.POINT:
                if len(self.points) != 1:
                    logger.error(f"Invalid points length (points = {self.points}) for {self._shape_type}")
                    raise WrongShapeError(f"Invalid points length (points = {self.points}) for {self._shape_type}")
                self.draw_vertex(vertex_path, 0)
            else:
                line_path.moveTo(self.points[0])
                self.draw_vertex(vertex_path, 0)
                for i, p in enumerate(self.points):
                    line_path.lineTo(p)
                    if self.is_selected:
                        self.draw_vertex(vertex_path, i)
                if self.is_closed:
                    line_path.lineTo(self.points[0])

            painter.drawPath(line_path)
            painter.drawPath(vertex_path)
            if self._vertex_fill_color is not None:
                painter.fillPath(vertex_path, self._vertex_fill_color)
            if self.is_fill:
                color = self.select_fill_color if self.is_selected else self.fill_color
                painter.fillPath(line_path, color)
