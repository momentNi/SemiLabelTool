import copy
import re
from typing import List, Tuple, Dict, Set

from PyQt5 import QtGui, QtCore
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QWidget, QApplication, QMenu

from core.configs.constants import Constants
from core.dto.cross_line import CrossLine
from core.dto.enums import ShapeType, CanvasMode, AutoLabelEditMode, AutoLabelShapeType, ShapeHighlightMode
from core.dto.exceptions import CanvasError
from core.dto.shape import Shape
from core.services.actions.canvas import *
from core.services.signals.canvas import *
from core.services.system import set_dirty, toggle_drawing_sensitive, scale_fit_window, scale_fit_width, update_combo_box
from utils.calculator import get_adjacent_points, rotate_point, intersection_point_with_box, distance
from utils.function import hex_to_rgb
from utils.logger import logger


class Canvas(QWidget):
    # Signal definition
    zoom_signal = QtCore.pyqtSignal(int, QtCore.QPointF)
    scroll_signal = QtCore.pyqtSignal(int, int)
    new_shape_signal = QtCore.pyqtSignal()
    show_shape_signal = QtCore.pyqtSignal(int, int, QtCore.QPointF)
    selection_changed_signal = QtCore.pyqtSignal(list)
    canvas_mode_changed_signal = QtCore.pyqtSignal()
    shape_moved_signal = QtCore.pyqtSignal()
    shape_rotated_signal = QtCore.pyqtSignal()
    drawing_polygon_signal = QtCore.pyqtSignal(bool)
    vertex_selected_signal = QtCore.pyqtSignal(bool)
    auto_labeling_marks_updated_signal = QtCore.pyqtSignal(list)

    def __init__(self):
        super().__init__(parent=CORE.Object.scroll_area)

        # =============================================================
        # =============== Constants or Basic Variables ================
        # =============================================================
        # Zoom Scale
        self.scale = 1.0
        # tiny value for dividing scale
        self.epsilon: float = 10.0
        # Text to show when the Canvas is loading something
        self.loading_text = "Loading..."
        # The angle of spinning wheel for loading animation
        self.loading_angle = 0

        # ==========================================
        # ============= Mode Variables =============
        # ==========================================
        # Canvas Operating mode. See CanvasMode Enum in enums.py
        self.canvas_mode: CanvasMode = CanvasMode.EDIT
        # Canvas Zooming mode. See ZoomMode Enum in enums.py
        self.zoom_mode: ZoomMode = ZoomMode.FIT_WINDOW
        # Shape type to create new shapes. See ShapeType Enum in enums.py
        self.create_mode: ShapeType = ShapeType.POLYGON
        # Auto Labeling mode. See AutoLabelEditMode and AutoLabelShapeType Enum in enums.py
        self.auto_labeling_mode: Tuple[AutoLabelEditMode, AutoLabelShapeType] = (AutoLabelEditMode.OFF, AutoLabelShapeType.OFF)

        # ============================================
        # ============= Status Variables =============
        # ============================================
        # Whether to fill the boxes
        self.is_fill_box: bool = False
        # Whether using auto labeling function
        self.is_auto_labeling: bool = False
        # Whether Canvas is loading something
        self.is_loading: bool = False
        # Whether Canvas is now moving a shape
        self.is_moving_shape: bool = False
        # Whether Canvas is now rotating a shape
        self.is_rotating_shape: bool = False
        # Whether cursor need to attract to the points or shapes
        self.is_snapping: bool = True
        # Set hide background - hide other shapes when some shapes are selected
        self.is_hide_background: bool = False
        # Whether the highlighting shape is selected
        self.is_highlight_shape_selected: bool = False
        # Whether the highlighting shape is hovered
        self.is_highlight_shape_hovered: bool = False

        # Whether some attributes are needed to show
        self.need_show_cross_line = True
        self.need_show_groups: bool = False
        self.need_show_texts: bool = True
        self.need_show_labels: bool = True
        self.need_show_scores: bool = True
        self.need_show_degrees: bool = False
        self.need_show_linking: bool = True

        # Status Variables for point, edge and shape
        self.highlight_shape: Shape | None = None
        self.prev_highlight_shape: Shape | None = None
        self.highlight_vertex: int | None = None
        self.prev_highlight_vertex: int | None = None
        self.highlight_edge: int | None = None
        self.prev_highlight_edge: int | None = None
        self.prev_point: QPointF | None = None
        self.prev_move_point: QPointF | None = None

        # =============================================
        # ============= History Variables =============
        # =============================================
        # Store zoom size for each shown file
        # key=filename, value=(zoom_mode, zoom_value)
        self.zoom_history: Dict[str, Tuple[ZoomMode, float]] = {}
        # Store scroll positions for each shown file
        # key=filename, value=scroll_value
        self.scroll_values: dict = {
            QtCore.Qt.Horizontal: {},
            QtCore.Qt.Vertical: {},
        }
        self.scroll_bars = {
            QtCore.Qt.Vertical: CORE.Object.scroll_area.verticalScrollBar(),
            QtCore.Qt.Horizontal: CORE.Object.scroll_area.horizontalScrollBar(),
        }
        self.scaler = {
            ZoomMode.FIT_WINDOW: scale_fit_window,
            ZoomMode.FIT_WIDTH: scale_fit_width,
            ZoomMode.MANUAL_ZOOM: lambda: 1,
        }

        # =============================================
        # ============= Canvas Variables ==============
        # =============================================
        # Cursor in Canvas
        self._cursor = QtCore.Qt.ArrowCursor
        # Painter for Canvas
        self._painter = QtGui.QPainter()
        # Cross line in Canvas
        self.cross_line = CrossLine()
        # Canvas Pixmap
        self.pixmap = QPixmap()
        # Operating Line, It means:
        #     Edge from last point to current if create_mode == ShapeType.POLYGON
        #     Diagonal line of the rectangle if create_mode == ShapeType.RECTANGLE
        #     The current line if create_mode == ShapeType.LINE
        #     The current point if create_mode == ShapeType.POINT
        self.line: Shape = Shape()
        # All shape objects in canvas of current image
        self.shapes: List[Shape] = []
        # Shape objects backups for undo operation
        self.shapes_backups: List[Shape] = []
        # Current operating Shape Object
        self.current: Shape | None = None
        # All shape objects selected in canvas of current image
        self.selected_shapes: List[Shape] = []
        # Copy of selected shapes
        self.selected_shapes_copy: List[Shape] = []
        # Record which shapes are visible(True) or not(False)
        self.visible_shapes: Dict[Shape, bool] = {}
        # Record the offset of horizontal and vertical of point
        self.offsets = QtCore.QPointF(), QtCore.QPointF()
        # Canvas Right click Menus
        # (without selection and dragging of shapes, with selection and dragging of shapes)
        self.menus = (QMenu(), QMenu())

        # Set Canvas options
        self.setMouseTracking(True)
        self.setFocusPolicy(QtCore.Qt.WheelFocus)

        self.__bind_signals()
        # TODO self.__init_actions()

    def __bind_signals(self):
        """
        Bind Signals with their corresponding functions
        """
        self.zoom_signal.connect(handle_zoom_request)
        self.scroll_signal.connect(handle_scroll_request)
        self.new_shape_signal.connect(handle_new_shape)
        self.show_shape_signal.connect(handle_show_shape)
        self.selection_changed_signal.connect(handle_selection_changed)
        self.shape_moved_signal.connect(set_dirty)
        self.shape_rotated_signal.connect(set_dirty)
        self.drawing_polygon_signal.connect(toggle_drawing_sensitive)
        # self.vertex_selected_signal.connect(self.actions.remove_point.setEnabled)
        # self.auto_labeling_marks_updated_signal.connect()

    def __init_actions(self):
        self.action_dict = {
            "canvas_fit_width": None,
            "canvas_fit_window": None,
        }
        for name, widget in self.action_dict.items():
            if getattr(CORE.Action, name, None) is not None:
                logger.warning(f"{self.objectName()} already exists in CORE.Action and will be skipped.")
                continue
            setattr(CORE.Action, name, widget)

    def is_shape_restorable(self) -> bool:
        """
        Check if shape can be restored from backup
        """
        return len(self.shapes_backups) >= 2

    def can_close_shape(self) -> bool:
        """
        Check if a shape can be closed (number of points > 2)
        """
        return self.canvas_mode == CanvasMode.CREATE and self.current and len(self.current) > 2

    def is_out_of_pixmap(self, pos: QtCore.QPointF) -> bool:
        """
        Check if a position is out of pixmap.

        Args:
            pos (QPointF): Target position.

        Returns:
            bool: Whether target position is out of pixmap.
        """
        if self.pixmap is None:
            return True
        w, h = self.pixmap.width(), self.pixmap.height()
        return not (0 <= pos.x() <= w - 1 and 0 <= pos.y() <= h - 1)

    def is_close_enough(self, p1: QtCore.QPointF, p2: QtCore.QPointF) -> bool:
        """
        Check if 2 points are close enough

        Divide by scale to allow more precision when zoomed in

        Args:
            p1: Point1
            p2: Point2

        Returns:
            bool: If 2 points are close enough
        """
        """"""
        #
        return distance(p1, p2) < (self.epsilon / self.scale)

    def is_no_shape(self):
        """
        Check if canvas has any shapes
        """
        return len(self.shapes) == 0

    def get_canvas_mode(self) -> str:
        if self.is_auto_labeling and self.auto_labeling_mode != (AutoLabelEditMode.OFF, AutoLabelShapeType.OFF):
            return "Auto Labeling"
        elif self.canvas_mode == CanvasMode.CREATE:
            return "Drawing"
        elif self.canvas_mode == CanvasMode.EDIT:
            return "Editing"
        else:
            return "Unknown"

    def get_image_offset_to_center(self) -> QtCore.QPointF:
        """
        Calculate offset to the center
        """
        if self.pixmap is None:
            return QtCore.QPointF()
        s = self.scale
        area = super().size()
        w, h = self.pixmap.width() * s, self.pixmap.height() * s
        area_width, area_height = area.width(), area.height()
        x = (area_width - w) / (2 * s) if area_width > w else 0
        y = (area_height - h) / (2 * s) if area_height > h else 0
        return QtCore.QPointF(x, y)

    def set_cross_line_style(self, need_show: bool, width: float, color: str, opacity: float) -> None:
        """
        Set the style of cross line in canvas

        Args:
            need_show: Whether the cross line need to be shown
            width: The width of cross line
            color: The color of cross line
            opacity: The opacity of cross line
        """
        self.need_show_cross_line = need_show
        self.cross_line.set_style(width, color, opacity)
        self.update()

    def set_point_offsets(self, point: QtCore.QPointF) -> None:
        """
        Calculate offsets of the point to the bounding rectangle of selected shapes

        Args:
            point: Target point
        """
        left = self.pixmap.width() - 1
        right = 0
        top = self.pixmap.height() - 1
        bottom = 0
        # find the union rectangle area for all selected shapes
        for shape in self.selected_shapes:
            rect = shape.get_bounding_rect()
            if rect.left() < left:
                left = rect.left()
            if rect.right() > right:
                right = rect.right()
            if rect.top() < top:
                top = rect.top()
            if rect.bottom() > bottom:
                bottom = rect.bottom()
        x1 = left - point.x()
        y1 = top - point.y()
        x2 = right - point.x()
        y2 = bottom - point.y()

        self.offsets = QtCore.QPointF(x1, y1), QtCore.QPointF(x2, y2)

    def set_last_label(self, text: str, flags: dict) -> Shape:
        """
        Set label and flags for last shape

        Args:
            text: label text
            flags: flags info for last shape

        Returns:
            Last shape object
        """
        if not text:
            logger.error(f"Label can't be empty: {text}")
            raise CanvasError(f"Label can't be empty: {text}")
        if self.is_auto_labeling:
            self.shapes[-1].label = self.auto_labeling_mode[0].value
        else:
            self.shapes[-1].label = text
        self.shapes[-1].flags = flags
        self.shapes_backups.pop()
        self.store_history_shapes()
        return self.shapes[-1]

    def set_shape_visible(self, shape: Shape, value: bool) -> None:
        """
        Set the visual status of shape

        Args:
            shape: Target shape object
            value: Visible(True) or not(False)
        """
        self.visible_shapes[shape] = value
        self.update()

    def set_auto_labeling_mode(self, edit_mode: AutoLabelEditMode, shape_type: AutoLabelShapeType) -> None:
        """
        Set the status of auto labeling

        Args:
            edit_mode: Edit mode for auto labeling
            shape_type: Shape type for auto labeling
        """
        if edit_mode == AutoLabelEditMode.OFF or shape_type == AutoLabelShapeType.OFF:
            self.is_auto_labeling = False
            self.auto_labeling_mode = (AutoLabelEditMode.OFF, AutoLabelShapeType.OFF)
        else:
            self.is_auto_labeling = True
            self.auto_labeling_mode = (edit_mode, shape_type)
            self.create_mode = ShapeType(shape_type.value)
            # TODO self.parent.toggle_draw_mode(
            #     False, mode.shape_type, disable_auto_labeling=False
            # )

    def set_auto_labeling_value(self, value=True) -> None:
        """
        Switch the status of auto labeling

        Args:
            value: Whether using auto labeling or not
        """
        self.is_auto_labeling = value
        if self.auto_labeling_mode is None:
            self.auto_labeling_mode = (AutoLabelEditMode.OFF, AutoLabelShapeType.OFF)
            # TODO self.parent.toggle_draw_mode(
            #     True, "rectangle", disable_auto_labeling=True
            # )

    def set_loading_status(self, is_loading: bool, loading_text: str = None) -> None:
        """
        Set the status of loading

        Args:
            is_loading: loading status
            loading_text: text to be shown
        """
        self.is_loading = is_loading
        if loading_text:
            self.loading_text = loading_text
        self.update()

    def set_editing(self, value=True) -> None:
        """
        Set editing mode for canvas

        Args:
            value: True for editing and False for drawing
        """
        self.canvas_mode = CanvasMode.EDIT if value else CanvasMode.CREATE
        # clear highlight and deselect shapes when user is drawing
        if not value:
            self.clear_highlight()
            self.deselect_shape()

    # ==================================================
    # ================ Shapes Methods ================
    # ==================================================
    def store_history_shapes(self) -> None:
        """
        Store the history shapes for undo operation
        """
        shapes_backup = []
        for shape in self.shapes:
            shapes_backup.append(shape.copy())
        # Store at most 10 shapes
        if len(self.shapes_backups) > 10:
            self.shapes_backups = self.shapes_backups[-11:]
        self.shapes_backups = shapes_backup

    def restore_shape(self) -> None:
        """
        Restore the last operating shape
        """
        if not self.is_shape_restorable:
            return
        self.shapes_backups.pop()
        shapes_backup = self.shapes_backups.pop()
        self.shapes = shapes_backup
        self.selected_shapes = []
        for shape in self.shapes:
            shape.selected = False
        self.update()

    def clear_highlight(self) -> None:
        """
        Clear highlight of shape/vertex/edge
        """
        if self.highlight_shape is not None:
            self.highlight_shape.highlight_clear()
            self.update()
        self.prev_highlight_shape = self.highlight_shape
        self.prev_highlight_vertex = self.highlight_vertex
        self.prev_highlight_edge = self.highlight_edge
        self.highlight_shape = None
        self.highlight_vertex = None
        self.highlight_edge = None

    def add_point_to_current_shape(self) -> None:
        """
        Add a point to current shape
        """
        shape: Shape = self.prev_highlight_shape
        edge: int = self.prev_highlight_edge
        point = self.prev_move_point
        if shape is None or edge is None or point is None:
            return
        shape.insert_point(edge, point)
        shape.highlight_vertex(edge, ShapeHighlightMode.MOVE_VERTEX)
        self.highlight_shape = shape
        self.highlight_vertex = edge
        self.highlight_edge = None
        self.is_moving_shape = True

    def remove_selected_point(self) -> None:
        """
        Remove a point from current shape
        """
        shape: Shape = self.prev_highlight_shape
        vertex: int = self.prev_highlight_vertex
        if shape is None or vertex is None:
            return
        shape.remove_point(vertex)
        shape.highlight_clear()
        self.highlight_shape = shape
        self.prev_highlight_vertex = None
        self.is_moving_shape = True

    def end_move(self, is_copy: bool) -> bool:
        """
        End of move

        Args:
            is_copy: Whether the ending shape is a copy

        Returns:
            Whether the operation is success
        """
        if self.selected_shapes is None or self.selected_shapes_copy is None:
            logger.error("No shape is selected")
            return False
        if len(self.selected_shapes_copy) != len(self.selected_shapes):
            logger.error("Selected shapes and selected shapes copy have different length")
            return False
        if is_copy:
            for i, shape in enumerate(self.selected_shapes_copy):
                self.shapes.append(shape)
                self.selected_shapes[i].is_selected = False
                self.selected_shapes[i] = shape
        else:
            for i, shape in enumerate(self.selected_shapes_copy):
                self.selected_shapes[i].points = shape.points
        self.selected_shapes_copy = []
        self.repaint()
        self.store_history_shapes()
        return True

    def hide_background_shapes(self, value: bool) -> None:
        """Set hide background
        Hide other shapes when some shapes are selected

        Args:
            value: The value of hiding background
        """
        self.is_hide_background = value
        if self.selected_shapes:
            # Only hide other shapes if there is a current selection.
            # Otherwise, the user will not be able to select a shape.
            self.update()

    def select_shapes(self, shapes: List[Shape]) -> None:
        """
        Set the shapes to be selected

        Args:
            shapes: Target shapes
        """
        self.is_hide_background = True
        self.selection_changed_signal.emit(shapes)
        self.update()

    def deselect_shape(self):
        """
        Clear the selection status of selected shapes
        """
        if self.selected_shapes:
            self.is_hide_background = False
            self.selection_changed_signal.emit([])
            self.is_highlight_shape_selected = False
            self.update()

    def select_shape_point(self, point: QtCore.QPointF, multiple_selection_mode: bool) -> None:
        """
        Select the first shape created which contains this point.

        Args:
            point: Point of shape.
            multiple_selection_mode: Whether support multiple selection.
        """
        if self.highlight_vertex is not None:
            vertex, shape = self.highlight_vertex, self.highlight_shape
            shape.highlight_vertex(vertex, ShapeHighlightMode.MOVE_VERTEX)
            if shape.shape_type == ShapeType.ROTATION:
                self.is_hide_background = True
                if shape not in self.selected_shapes:
                    if multiple_selection_mode:
                        self.selection_changed_signal.emit(self.selected_shapes + [shape])
                    else:
                        self.selection_changed_signal.emit([shape])
                    self.is_highlight_shape_selected = False
                else:
                    self.is_highlight_shape_selected = True
                self.set_point_offsets(point)
                return
        else:
            for shape in reversed(self.shapes):
                if self.visible_shapes.get(shape, True) and len(shape.points) > 1 and shape.contains_point(point):
                    self.is_hide_background = True
                    if shape not in self.selected_shapes:
                        if multiple_selection_mode:
                            self.selection_changed_signal.emit(self.selected_shapes + [shape])
                        else:
                            self.selection_changed_signal.emit([shape])
                        self.is_highlight_shape_selected = False
                    else:
                        self.is_highlight_shape_selected = True
                    self.set_point_offsets(point)
                    return
        self.deselect_shape()

    def delete_selected_shapes(self) -> List[Shape]:
        """
        Delete selected shapes

        Returns:
            Deleted shapes
        """
        deleted_shapes = []
        if self.selected_shapes:
            for shape in self.selected_shapes:
                self.shapes.remove(shape)
                deleted_shapes.append(shape)
            self.store_history_shapes()
            self.selected_shapes = []
            self.update()
        return deleted_shapes

    def delete_shape(self, shape):
        """
        Delete all shapes in current canvas
        """
        if shape in self.selected_shapes:
            self.selected_shapes.remove(shape)
        if shape in self.shapes:
            self.shapes.remove(shape)
        self.store_history_shapes()
        self.update()

    def duplicate_selected_shapes(self):
        """
        Duplicate selected shapes

        Returns:
            selected shapes
        """
        if self.selected_shapes:
            self.selected_shapes_copy = [s.copy() for s in self.selected_shapes]
            self.bounded_shift_shapes(self.selected_shapes_copy)
            self.end_move(is_copy=True)
        return self.selected_shapes

    def move_by_keyboard(self, offset: QtCore.QPointF) -> None:
        """
        Move selected shapes by an offset (using keyboard)

        Args:
            offset (QPointF): Offset QPointF
        """
        if self.selected_shapes:
            self.bounded_move_shapes(self.selected_shapes, self.prev_point + offset)
            self.repaint()
            self.is_moving_shape = True

    def rotate_by_keyboard(self, theta: float) -> None:
        """
        Rotate selected shapes by theta (using keyboard)

        Args:
            theta: Rotation degree
        """
        if self.selected_shapes:
            for i, shape in enumerate(self.selected_shapes):
                if shape.shape_type == ShapeType.ROTATION:
                    self.bounded_rotate_shapes(i, shape, theta)
                    self.repaint()
                    self.is_rotating_shape = True

    def bounded_move_vertex(self, pos: QtCore.QPointF) -> None:
        """
        Move a vertex.

        Adjust position to be bounded by pixmap border.

        Args:
            pos: Target position of movement.
        """
        operating_vertex_index, operating_shape = self.highlight_vertex, self.highlight_shape
        operating_point = operating_shape[operating_vertex_index]
        if self.is_out_of_pixmap(pos) and operating_shape.shape_type != ShapeType.ROTATION:
            pos = intersection_point_with_box(operating_point, pos, self.pixmap.width(), self.pixmap.height())

        if operating_shape.shape_type == ShapeType.ROTATION:
            opposite_vertex_index = (operating_vertex_index + 2) % 4
            # Get the other 3 points after transformed
            p2, p3, p4 = get_adjacent_points(operating_shape.direction, operating_shape[opposite_vertex_index], pos, operating_vertex_index)
            # Move 4 pixel one by one
            operating_shape.move_point(operating_vertex_index, pos - operating_point)
            left_vertex_index = (operating_vertex_index + 1) % 4
            right_vertex_index = (operating_vertex_index + 3) % 4
            operating_shape[left_vertex_index] = p2
            operating_shape[right_vertex_index] = p4
            operating_shape.close_shape()
        elif operating_shape.shape_type == ShapeType.RECTANGLE:
            shift_pos = pos - operating_point
            operating_shape.move_point(operating_vertex_index, shift_pos)
            left_index = (operating_vertex_index + 1) % 4
            right_index = (operating_vertex_index + 3) % 4
            if operating_vertex_index % 2 == 0:
                right_shift = QtCore.QPointF(shift_pos.x(), 0)
                left_shift = QtCore.QPointF(0, shift_pos.y())
            else:
                left_shift = QtCore.QPointF(shift_pos.x(), 0)
                right_shift = QtCore.QPointF(0, shift_pos.y())
            operating_shape.move_point(right_index, right_shift)
            operating_shape.move_point(left_index, left_shift)
        else:
            operating_shape.move_point(operating_vertex_index, pos - operating_point)

    def bounded_move_shapes(self, shapes: List[Shape], pos: QtCore.QPointF) -> bool:
        """
        Move shapes

        Adjust position to be bounded by pixmap border.

        Args:
            shapes: Selected shapes
            pos: Target position

        Returns:
            bool: Whether the movement operation is success.
        """
        rotation_shapes = [shape.shape_type for shape in shapes if shape.shape_type == ShapeType.ROTATION]

        # Forbid movement if selected shapes are not in the same shape type
        if (self.is_out_of_pixmap(pos) and len(rotation_shapes) == 0) or (0 < len(rotation_shapes) != len(shapes)):
            logger.warning("Selected shapes are not in the same shape type")
            return False

        if len(rotation_shapes) == 0:
            o1 = pos + self.offsets[0]
            if self.is_out_of_pixmap(o1):
                pos -= QtCore.QPointF(min(0, int(o1.x())), min(0, int(o1.y())))
            o2 = pos + self.offsets[1]
            if self.is_out_of_pixmap(o2):
                pos += QtCore.QPointF(min(0, int(self.pixmap.width() - o2.x())), min(0, int(self.pixmap.height() - o2.y())))
        delta = pos - self.prev_point
        if delta:
            for shape in shapes:
                shape.move_shape(delta)
            self.prev_point = pos
            return True
        return False

    def bounded_rotate_shapes(self, i: int, shape: Shape, theta: float) -> bool:
        """
        Rotate shapes.

        Adjust position to be bounded by pixmap border

        Args:
            i: Point tobe rotated
            shape: Shape object tobe rotated
            theta: Rotation Angle

        Returns:
            bool: Whether the rotation operation is success.
        """
        new_shape = copy.deepcopy(shape)
        if len(shape.points) == 2:
            new_shape.points[0] = shape.points[0]
            new_shape.points[1] = QtCore.QPointF((shape.points[0].x() + shape.points[1].x()) / 2, shape.points[0].y())
            new_shape.points.append(shape.points[1])
            new_shape.points.append(QtCore.QPointF(shape.points[1].x(), (shape.points[0].y() + shape.points[1].y()) / 2))
        center = QtCore.QPointF((new_shape.points[0].x() + new_shape.points[2].x()) / 2, (new_shape.points[0].y() + new_shape.points[2].y()) / 2)
        for j, p in enumerate(new_shape.points):
            pos = rotate_point(p, center, theta)
            if self.is_out_of_pixmap(pos):
                # No need to rotate
                logger.warning(f"Rotation position: {pos} is out of pixmap.")
                return False
            new_shape.points[j] = pos
        new_shape.direction = (new_shape.direction - theta) % (2 * math.pi)
        self.selected_shapes[i].points = new_shape.points
        self.selected_shapes[i].direction = new_shape.direction
        return True

    def bounded_shift_shapes(self, shapes: List[Shape]) -> None:
        """
        Shift shapes by an offset.

        Adjust positions to be bounded by pixmap borders

        Args:
            shapes: Shapes tobe shifted
        """
        # Try to move in one direction, and if it fails in another.
        # Give up if both fail.
        point = shapes[0][0]
        offset = QtCore.QPointF(2.0, 2.0)
        self.offsets = QtCore.QPointF(), QtCore.QPointF()
        self.prev_point = point
        if not self.bounded_move_shapes(shapes, point - offset):
            self.bounded_move_shapes(shapes, point + offset)

    def finalise_shape(self) -> None:
        """
        Finish drawing for a shape
        """
        if not self.current:
            logger.error(f"No shape to finalise: {self.current}")
            raise CanvasError(f"No shape to finalise: {self.current}")
        if self.is_auto_labeling and self.auto_labeling_mode != (AutoLabelEditMode.OFF, AutoLabelShapeType.OFF):
            self.current.label = self.auto_labeling_mode[0].value
        self.current.close_shape()
        self.shapes.append(self.current)
        self.store_history_shapes()
        self.current = None
        self.is_hide_background = False
        self.new_shape_signal.emit()
        self.update()
        if self.is_auto_labeling:
            self.update_auto_labeling_marks()

    # ==================================================
    # ================ Canvas Methods ================
    # ==================================================
    def override_cursor(self, cursor: Qt.CursorShape) -> None:
        """
        Override the type of cursor to target type

        Args:
            cursor: Target cursor type
        """
        self.restore_cursor()
        self._cursor = cursor
        QApplication.setOverrideCursor(cursor)

    @staticmethod
    def restore_cursor() -> None:
        """
        Restore the cursor type to default
        """
        QApplication.restoreOverrideCursor()

    def reset_canvas(self) -> None:
        """
        Reset Canvas status to startup
        """
        self.restore_cursor()
        self.pixmap = None
        self.shapes_backups = []
        self.update()

    def transform_pos(self, point: QtCore.QPointF) -> QtCore.QPointF:
        """
        Convert from widget-logical coordinates to painter-logical ones.

        Args:
            point(QPointF) : widget-logical coordinates

        Returns:
            QPointF: Painter-logical coordinates
        """
        return point / self.scale - self.get_image_offset_to_center()

    def undo_last_line(self) -> None:
        """
        Undo the last drawing operation and revert to the previous state.
        """
        if not self.shapes:
            logger.error(f"There is no Shape: {self.shapes}")
            raise CanvasError(f"There is no Shape: {self.shapes}")
        self.current = self.shapes.pop()
        self.current.is_closed = False
        if self.create_mode in (ShapeType.POLYGON, ShapeType.LINE_STRIP):
            self.line.points = [self.current[-1], self.current[0]]
        elif self.create_mode in (ShapeType.RECTANGLE, ShapeType.LINE, ShapeType.CIRCLE, ShapeType.ROTATION):
            self.current.points = self.current.points[0:1]
        elif self.create_mode == ShapeType.POINT:
            self.current = None
        self.drawing_polygon_signal.emit(True)

    def undo_last_point(self) -> None:
        """
        Undo the last point of the current polygon.
        If the current polygon does not exist or is already closed, it does nothing.
        """
        if not self.current or self.current.is_closed:
            return
        self.current.pop_point()
        if len(self.current) > 0:
            self.line[0] = self.current[-1]
        else:
            self.current = None
            self.drawing_polygon_signal.emit(False)
        self.update()

    def load_pixmap(self, pixmap: QPixmap, clear_shapes: bool = True) -> None:
        """
        Load pixmap of current image to Canvas

        Args:
            pixmap: Pixmap of current image
            clear_shapes: Whether it is needed to clear shapes
        """
        self.pixmap = pixmap
        if clear_shapes:
            self.shapes = []
        self.update()

    def load_shapes(self, shapes: List[Shape], replace: bool = True) -> None:
        """
        Load shapes into the current list.

        Args:
            shapes (List[Shape]): The list of shapes to be loaded.
            replace (bool): A boolean indicating whether to replace the existing shape list or extend it. Default is True.
        """
        if replace:
            self.shapes = list(shapes)
        else:
            self.shapes.extend(shapes)
        self.store_history_shapes()
        self.current = None
        self.highlight_shape = None
        self.highlight_vertex = None
        self.highlight_edge = None
        self.update()

    def load_labels(self, shapes: List):
        s = []
        for shape in shapes:
            label = shape["label"]
            score = shape.get("score", None)
            points = shape["points"]
            shape_type = shape["shape_type"]
            flags = shape["flags"]
            group_id = shape["group_id"]
            description = shape.get("description", "")
            is_difficult = shape.get("difficult", False)
            attributes = shape.get("attributes", {})
            direction = shape.get("direction", 0)
            kie_linking = shape.get("kie_linking", [])
            other_data = shape["other_data"]

            if label in CORE.Variable.hidden_class_list or not points:
                # skip point-empty shape
                continue

            shape = Shape(
                label=label,
                score=score,
                shape_type=shape_type,
                group_id=group_id,
                description=description,
                is_difficult=is_difficult,
                direction=direction,
                attributes=attributes,
                kie_linking=kie_linking,
            )
            for x, y in points:
                shape.add_point(QtCore.QPointF(x, y))
            shape.close_shape()

            default_flags = {}
            if CORE.Variable.settings.get("label_flags"):
                label_flags = CORE.Variable.settings.get("label_flags")
                for pattern, keys in label_flags.items():
                    if re.match(pattern, label):
                        for key in keys:
                            default_flags[key] = False
            shape.flags = default_flags
            if flags:
                shape.flags.update(flags)
            shape.other_data = other_data

            s.append(shape)
        update_combo_box()
        self.load_shapes(s)

    # ==================================================
    # ================= Group Methods ==================
    # ==================================================
    def generate_new_group_id(self) -> int:
        """
        Generate a new group ID.

        This method iterates through all shapes (self.shapes) to find the current maximum group ID (max_group_id).
        Returns a new group ID that is one greater than the maximum group ID.
        If none of the shapes have a group ID, it returns 1, ensuring that the newly generated group ID is unique.

        Returns:
            int: The new group ID.
        """
        max_group_id = 0
        for shape in self.shapes:
            if shape.group_id is not None:
                max_group_id = max(max_group_id, shape.group_id)
        return max_group_id + 1

    def merge_group_ids(self, group_ids: Set[int], new_group_id: int) -> None:
        """
        Merge multiple shapes' group IDs into a new one.

        Args:
            group_ids (Set[int]): A set of group IDs to be merged.
            new_group_id (int): The new group ID to assign to the shapes.
        """
        for shape in self.shapes:
            if shape.group_id in group_ids:
                shape.group_id = new_group_id

    def group_selected_shapes(self):
        """
        Group selected shapes by assigning them a common group ID.
        """
        if len(self.selected_shapes) == 0:
            return

        # List all group ids for selected shapes
        group_ids = set()
        has_non_group_shape = False
        for shape in self.selected_shapes:
            if shape.group_id is not None:
                group_ids.add(shape.group_id)
            else:
                has_non_group_shape = True

        # If there is at least 1 shape having a group id,
        # use that id as the new group id. Otherwise, generate a new group_id
        if len(group_ids) > 0:
            new_group_id = min(group_ids)
        else:
            new_group_id = self.generate_new_group_id()

        # Merge group ids
        if len(group_ids) > 1:
            self.merge_group_ids(group_ids=group_ids, new_group_id=new_group_id)
        # Assign new_group_id to non-group shapes
        if has_non_group_shape:
            for shape in self.selected_shapes:
                if shape.group_id is None:
                    shape.group_id = new_group_id

        self.update()

    def ungroup_selected_shapes(self):
        """Ungroup selected shapes"""
        if len(self.selected_shapes) == 0:
            return

        # List all group ids for selected shapes
        group_ids = set()
        for shape in self.selected_shapes:
            if shape.group_id is not None:
                group_ids.add(shape.group_id)

        for group_id in group_ids:
            for shape in self.shapes:
                if shape.group_id == group_id:
                    shape.group_id = None

        self.update()

    # ==================================================
    # =============== Auto Label Methods ===============
    # ==================================================
    def update_auto_labeling_marks(self):
        """
        Update the auto labeling marks
        """
        marks = []
        for shape in self.shapes:
            if shape.label == AutoLabelEditMode.ADD.value:
                if shape.shape_type == AutoLabelShapeType.POINT:
                    marks.append({
                        "type": shape.shape_type.name,
                        "data": [
                            int(shape.points[0].x()),
                            int(shape.points[0].y()),
                        ],
                        "label": 1,
                    })
                elif shape.shape_type == AutoLabelShapeType.RECTANGLE:
                    marks.append({
                        "type": shape.shape_type.name,
                        "data": [
                            int(shape.points[0].x()),
                            int(shape.points[0].y()),
                            int(shape.points[2].x()),
                            int(shape.points[2].y()),
                        ],
                        "label": 1,
                    })
            elif shape.label == AutoLabelEditMode.REMOVE.name:
                if shape.shape_type == AutoLabelShapeType.POINT:
                    marks.append({
                        "type": shape.shape_type.name,
                        "data": [
                            int(shape.points[0].x()),
                            int(shape.points[0].y()),
                        ],
                        "label": 0,
                    })
                elif shape.shape_type == AutoLabelShapeType.RECTANGLE:
                    marks.append({
                        "type": shape.shape_type.name,
                        "data": [
                            int(shape.points[0].x()),
                            int(shape.points[0].y()),
                            int(shape.points[2].x()),
                            int(shape.points[2].y()),
                        ],
                        "label": 0,
                    })
        self.auto_labeling_marks_updated_signal.emit(marks)

    # ==================================================
    # ================ Override Methods ================
    # ==================================================
    def enterEvent(self, _):
        self.override_cursor(self._cursor)

    def leaveEvent(self, _):
        # self.un_highlight()
        self.restore_cursor()

    def focusOutEvent(self, _):
        self.restore_cursor()

    def sizeHint(self):
        return self.minimumSizeHint()

    def minimumSizeHint(self):
        if self.pixmap:
            return self.scale * self.pixmap.size()
        return super().minimumSizeHint()

    def wheelEvent(self, ev):
        delta = ev.angleDelta()
        if QtCore.Qt.ControlModifier == int(ev.modifiers()):
            # with Ctrl/Command key, zoom
            self.zoom_signal.emit(delta.y(), ev.pos())
        else:
            # scroll
            self.scroll_signal.emit(delta.x(), QtCore.Qt.Horizontal)
            self.scroll_signal.emit(delta.y(), QtCore.Qt.Vertical)
        ev.accept()

    def mouseMoveEvent(self, ev):
        if self.is_loading:
            return
        try:
            pos = self.transform_pos(ev.localPos())
        except AttributeError as e:
            logger.error(f"transform position failed: {e}")
            return

        self.show_shape_signal.emit(-1, -1, pos)

        self.prev_move_point = pos
        self.repaint()
        self.restore_cursor()

        # Polygon drawing
        if self.canvas_mode == CanvasMode.CREATE:
            self.line.line_color = QtGui.QColor(*hex_to_rgb(self.cross_line.color))
            self.line.shape_type = self.create_mode

            self.override_cursor(QtCore.Qt.CrossCursor)
            if not self.current:
                return

            if self.create_mode == ShapeType.RECTANGLE:
                shape_width = abs(self.current[0].x() - pos.x())
                shape_height = abs(self.current[0].y() - pos.y())
                self.show_shape_signal.emit(shape_width, shape_height, pos)

            color = QtGui.QColor(0, 0, 255)
            if self.is_out_of_pixmap(pos) and self.create_mode != ShapeType.ROTATION:
                # Don't allow the user to draw outside the pixmap, except for rotation.
                # Project the point to the pixmap's edges.
                pos = intersection_point_with_box(self.current[-1], pos, self.pixmap.width(), self.pixmap.height())
            elif self.is_snapping and len(self.current) > 1 and self.create_mode == ShapeType.POLYGON and self.is_close_enough(pos, self.current[0]):
                # Attract line to starting point and colorise to alert the user.
                pos = self.current[0]
                self.override_cursor(QtCore.Qt.PointingHandCursor)
                self.current.highlight_vertex(0, ShapeHighlightMode.NEAR_VERTEX)
            elif self.create_mode == ShapeType.ROTATION and len(self.current) > 0 and self.is_close_enough(pos, self.current[0]):
                pos = self.current[0]
                color = self.current.line_color
                self.override_cursor(QtCore.Qt.PointingHandCursor)
                self.current.highlight_vertex(0, ShapeHighlightMode.NEAR_VERTEX)

            if self.create_mode in (ShapeType.POLYGON, ShapeType.LINE_STRIP):
                self.line[0] = self.current[-1]
                self.line[1] = pos
            elif self.create_mode == ShapeType.RECTANGLE:
                self.line.points = [self.current[0], pos]
                self.line.is_closed = True
            elif self.create_mode == ShapeType.ROTATION:
                self.line[1] = pos
                self.line.line_color = color
            elif self.create_mode == ShapeType.CIRCLE:
                self.line.points = [self.current[0], pos]
                self.line.shape_type = ShapeType.CIRCLE
            elif self.create_mode == ShapeType.LINE:
                self.line.points = [self.current[0], pos]
                self.line.is_closed = True
            elif self.create_mode == ShapeType.POINT:
                self.line.points = [self.current[0]]
                self.line.is_closed = True

            self.repaint()
            self.current.highlight_clear()
            return

        # Polygon copy moving
        if QtCore.Qt.RightButton & ev.buttons():
            if self.selected_shapes_copy and self.prev_point:
                self.override_cursor(QtCore.Qt.ClosedHandCursor)
                self.bounded_move_shapes(self.selected_shapes_copy, pos)
                self.repaint()
            elif self.selected_shapes:
                self.selected_shapes_copy = [s.copy() for s in self.selected_shapes]
                self.repaint()
            return

        # Polygon/Vertex moving.
        if QtCore.Qt.LeftButton & ev.buttons():
            if self.highlight_vertex is not None:
                try:
                    self.bounded_move_vertex(pos)
                    self.repaint()
                    self.is_moving_shape = True
                except IndexError:
                    return
                if self.highlight_shape.shape_type == ShapeType.RECTANGLE:
                    p1 = self.highlight_shape[0]
                    p2 = self.highlight_shape[2]
                    shape_width = abs(p2.x() - p1.x())
                    shape_height = abs(p2.y() - p1.y())
                    self.show_shape_signal.emit(shape_width, shape_height, pos)
            elif self.selected_shapes and self.prev_point:
                self.override_cursor(QtCore.Qt.ClosedHandCursor)
                self.bounded_move_shapes(self.selected_shapes, pos)
                self.repaint()
                self.is_moving_shape = True
                if self.selected_shapes[-1].shape_type == ShapeType.RECTANGLE:
                    p1 = self.selected_shapes[-1][0]
                    p2 = self.selected_shapes[-1][2]
                    shape_width = abs(p2.x() - p1.x())
                    shape_height = abs(p2.y() - p1.y())
                    self.show_shape_signal.emit(shape_width, shape_height, pos)
            return

        # Just hovering over the canvas, 2 possibilities:
        # - Highlight shapes
        # - Highlight vertex
        # Update shape/vertex fill and tooltip value accordingly.
        self.setToolTip("Image")
        for shape in reversed([s for s in self.shapes if self.visible_shapes.get(s, True)]):
            # Look for a nearby vertex to highlight. If that fails,
            # check if we happen to be inside a shape.
            vertex_index = shape.get_nearest_vertex(pos, self.epsilon / self.scale)
            edge_index = shape.get_nearest_edge(pos, self.epsilon / self.scale)
            if vertex_index is not None:
                if self.highlight_vertex:
                    self.highlight_shape.highlight_clear()
                self.prev_highlight_vertex = self.highlight_vertex = vertex_index
                self.prev_highlight_shape = self.highlight_shape = shape
                self.prev_highlight_edge = self.highlight_edge
                self.highlight_shape = None
                shape.highlight_vertex(vertex_index, ShapeHighlightMode.MOVE_VERTEX)
                self.override_cursor(QtCore.Qt.PointingHandCursor)
                self.setToolTip(f"Click & drag to move point of shape '{shape.label}'")
                self.setStatusTip(self.toolTip())
                self.update()
                break
            if edge_index is not None and shape.can_add_point():
                if self.highlight_vertex is not None:
                    self.highlight_shape.highlight_clear()
                self.prev_highlight_vertex = self.highlight_vertex
                self.highlight_vertex = None
                self.prev_highlight_shape = self.highlight_shape = shape
                self.prev_highlight_edge = self.highlight_edge = edge_index
                self.override_cursor(QtCore.Qt.PointingHandCursor)
                self.setToolTip(f"Click to create point of shape '{shape.label}'")
                self.setStatusTip(self.toolTip())
                self.update()
                break
            if len(shape.points) > 1 and shape.contains_point(pos):
                if self.highlight_vertex is not None:
                    self.highlight_shape.highlight_clear()
                self.prev_highlight_vertex = self.highlight_vertex
                self.highlight_vertex = None
                self.prev_highlight_shape = self.highlight_shape = shape
                self.prev_highlight_edge = self.highlight_edge
                self.highlight_edge = None
                if shape.group_id and shape.shape_type == ShapeType.RECTANGLE:
                    self.setToolTip(f"Click & drag to move shape '{shape.label} {shape.group_id}'")
                else:
                    self.setToolTip(f"Click & drag to move shape '{shape.label}'")
                self.setStatusTip(self.toolTip())
                self.override_cursor(QtCore.Qt.OpenHandCursor)
                if self.is_highlight_shape_hovered:
                    group_mode = int(ev.modifiers()) == QtCore.Qt.ControlModifier
                    self.select_shape_point(pos, multiple_selection_mode=group_mode)
                self.update()

                if shape.shape_type == ShapeType.RECTANGLE:
                    p1 = self.highlight_shape[0]
                    p2 = self.highlight_shape[2]
                    shape_width = abs(p2.x() - p1.x())
                    shape_height = abs(p2.y() - p1.y())
                    self.show_shape_signal.emit(shape_width, shape_height, pos)
                break
        else:
            # Nothing found, clear highlights, reset state.
            self.clear_highlight()
        self.vertex_selected_signal.emit(self.highlight_vertex is not None)

    def mousePressEvent(self, ev):
        if self.is_loading:
            return
        pos = self.transform_pos(ev.localPos())
        if ev.button() == QtCore.Qt.LeftButton:
            if self.canvas_mode == CanvasMode.CREATE:
                if self.current:
                    # Add point to existing shape.
                    if self.create_mode == ShapeType.POLYGON:
                        self.current.add_point(self.line[1])
                        self.line[0] = self.current[-1]
                        if self.current.is_closed:
                            self.finalise_shape()
                    elif self.create_mode in (ShapeType.CIRCLE, ShapeType.LINE):
                        if len(self.current.points) != 1:
                            logger.error(f"Invalid point length of current shape: {len(self.current.points)}")
                            raise CanvasError(f"Invalid point length of current shape: {len(self.current.points)}")
                        self.current.points = self.line.points
                        self.finalise_shape()
                    elif self.create_mode == ShapeType.RECTANGLE:
                        if not self.current.is_reach_max_points():
                            init_pos = self.current[0]
                            min_x = init_pos.x()
                            min_y = init_pos.y()
                            target_pos = self.line[1]
                            max_x = target_pos.x()
                            max_y = target_pos.y()
                            self.current.add_point(QtCore.QPointF(max_x, min_y))
                            self.current.add_point(target_pos)
                            self.current.add_point(QtCore.QPointF(min_x, max_y))
                            self.finalise_shape()
                    elif self.create_mode == ShapeType.ROTATION:
                        init_pos = self.current[0]
                        min_x = init_pos.x()
                        min_y = init_pos.y()
                        target_pos = self.line[1]
                        max_x = target_pos.x()
                        max_y = target_pos.y()
                        self.current.add_point(QtCore.QPointF(max_x, min_y))
                        self.current.add_point(target_pos)
                        self.current.add_point(QtCore.QPointF(min_x, max_y))
                        self.current.add_point(init_pos)
                        self.line[0] = self.current[-1]
                        if self.current.is_closed:
                            self.finalise_shape()
                    elif self.create_mode == ShapeType.LINE_STRIP:
                        self.current.add_point(self.line[1])
                        self.line[0] = self.current[-1]
                        if int(ev.modifiers()) == QtCore.Qt.ControlModifier:
                            self.finalise_shape()
                    if not self.is_auto_labeling and self.create_mode in (ShapeType.RECTANGLE, ShapeType.ROTATION, ShapeType.CIRCLE, ShapeType.LINE, ShapeType.POINT):
                        self.canvas_mode_changed_signal.emit()
                elif not self.is_out_of_pixmap(pos):
                    # Create new shape.
                    self.current = Shape(shape_type=self.create_mode)
                    self.current.add_point(pos)
                    if self.create_mode == ShapeType.POINT:
                        self.finalise_shape()
                    else:
                        if self.create_mode == ShapeType.CIRCLE:
                            self.current.shape_type = ShapeType.CIRCLE
                        self.line.points = [pos, pos]
                        self.is_hide_background = True
                        self.drawing_polygon_signal.emit(True)
                        self.update()
                elif self.is_out_of_pixmap(pos) and self.create_mode == ShapeType.ROTATION:
                    # Create new shape.
                    self.current = Shape(shape_type=self.create_mode)
                    self.current.add_point(pos)
                    self.line.points = [pos, pos]
                    self.is_hide_background = True
                    self.drawing_polygon_signal.emit(True)
                    self.update()
            elif self.canvas_mode == CanvasMode.EDIT:
                if self.highlight_edge is not None:
                    self.add_point_to_current_shape()
                elif (self.highlight_vertex is not None and int(ev.modifiers()) == QtCore.Qt.ShiftModifier
                      and self.highlight_shape.shape_type not in (ShapeType.RECTANGLE, ShapeType.ROTATION, ShapeType.LINE)):
                    # Delete point if: left-click + SHIFT on a point
                    self.remove_selected_point()

                group_mode = int(ev.modifiers()) == QtCore.Qt.ControlModifier
                self.select_shape_point(pos, multiple_selection_mode=group_mode)
                self.prev_point = pos
                self.repaint()
        elif ev.button() == QtCore.Qt.RightButton and self.canvas_mode == CanvasMode.EDIT:
            group_mode = int(ev.modifiers()) == QtCore.Qt.ControlModifier
            if not self.selected_shapes or (
                    self.highlight_shape is not None and self.highlight_shape not in self.selected_shapes):
                self.select_shape_point(pos, multiple_selection_mode=group_mode)
                self.repaint()
            self.prev_point = pos

    def mouseReleaseEvent(self, ev):
        if self.is_loading:
            return
        if ev.button() == QtCore.Qt.RightButton:
            menu = self.menus[len(self.selected_shapes_copy) > 0]
            self.restore_cursor()
            if not menu.exec_(self.mapToGlobal(ev.pos())) and self.selected_shapes_copy:
                # Cancel the move by deleting the shadow copy.
                self.selected_shapes_copy = []
                self.repaint()
        elif ev.button() == QtCore.Qt.LeftButton:
            if self.canvas_mode == CanvasMode.EDIT:
                if self.highlight_shape is not None and self.is_highlight_shape_selected and not self.is_moving_shape:
                    self.selection_changed_signal.emit([x for x in self.selected_shapes if x != self.highlight_shape])

        if self.is_moving_shape and self.highlight_shape:
            index = self.shapes.index(self.highlight_shape)
            if self.shapes_backups[-1][index].points != self.shapes[index].points:
                self.store_history_shapes()
                self.shape_moved_signal.emit()

            self.is_moving_shape = False

    def mouseDoubleClickEvent(self, _):
        if self.is_loading:
            return
        # We need at least 4 points here, since the mousePress handler
        # adds an extra one before this handler is called.
        if self.can_close_shape() and len(self.current) > 3:
            self.current.pop_point()
            self.finalise_shape()

    def keyPressEvent(self, ev):
        modifiers = ev.modifiers()
        key = ev.key()
        if self.canvas_mode == CanvasMode.CREATE:
            if key == QtCore.Qt.Key_Escape and self.current:
                self.current = None
                self.drawing_polygon_signal.emit(False)
                self.update()
            elif key == QtCore.Qt.Key_Return and self.can_close_shape():
                self.finalise_shape()
            elif modifiers == QtCore.Qt.AltModifier:
                self.is_snapping = False
        elif self.canvas_mode == CanvasMode.EDIT:
            if key == QtCore.Qt.Key_Up:
                self.move_by_keyboard(QtCore.QPointF(0.0, -5.0))
            elif key == QtCore.Qt.Key_Down:
                self.move_by_keyboard(QtCore.QPointF(0.0, 5.0))
            elif key == QtCore.Qt.Key_Left:
                self.move_by_keyboard(QtCore.QPointF(-5.0, 0.0))
            elif key == QtCore.Qt.Key_Right:
                self.move_by_keyboard(QtCore.QPointF(5.0, 0.0))
            elif key == QtCore.Qt.Key_Z:
                self.rotate_by_keyboard(0.1)
            elif key == QtCore.Qt.Key_X:
                self.rotate_by_keyboard(0.01)
            elif key == QtCore.Qt.Key_C:
                self.rotate_by_keyboard(-0.01)
            elif key == QtCore.Qt.Key_V:
                self.rotate_by_keyboard(-0.1)

    def keyReleaseEvent(self, ev):
        modifiers = ev.modifiers()
        if self.canvas_mode == CanvasMode.CREATE:
            if int(modifiers) == 0:
                self.is_snapping = True
        elif self.canvas_mode == CanvasMode.EDIT:
            # NOTE: Temporary fix to avoid ValueError
            # when the selected shape is not in the shapes list
            if (self.is_moving_shape or self.is_rotating_shape) and self.selected_shapes and self.selected_shapes[0] in self.shapes:
                index = self.shapes.index(self.selected_shapes[0])
                if self.shapes_backups[-1][index].points != self.shapes[index].points:
                    self.store_history_shapes()
                    if self.is_moving_shape:
                        self.shape_moved_signal.emit()
                    if self.is_rotating_shape:
                        self.shape_rotated_signal.emit()

                if self.is_moving_shape:
                    self.is_moving_shape = False
                if self.is_rotating_shape:
                    self.is_rotating_shape = False

    def paintEvent(self, event):
        if self.pixmap is None or self.pixmap.width() == 0 or self.pixmap.height() == 0:
            super().paintEvent(event)
            return

        p = self._painter
        p.begin(self)
        p.setRenderHint(QtGui.QPainter.Antialiasing)
        p.setRenderHint(QtGui.QPainter.SmoothPixmapTransform)
        p.setRenderHint(QtGui.QPainter.HighQualityAntialiasing)

        p.scale(self.scale, self.scale)
        p.translate(self.get_image_offset_to_center())

        p.drawPixmap(0, 0, self.pixmap)
        Constants.SHAPE_SCALE = self.scale

        # Draw loading/waiting screen
        if self.is_loading:
            # Draw a semi-transparent rectangle
            p.setPen(Qt.NoPen)
            p.setBrush(QtGui.QColor(0, 0, 0, 20))
            p.drawRect(self.pixmap.rect())

            # Draw a spinning wheel
            p.setPen(QtGui.QColor(255, 255, 255))
            p.setBrush(Qt.NoBrush)
            p.save()
            p.translate(self.pixmap.width() / 2, self.pixmap.height() / 2 - 50)
            p.rotate(self.loading_angle)
            p.drawEllipse(-20, -20, 40, 40)
            p.drawLine(0, 0, 0, -20)
            p.restore()
            self.loading_angle += 30
            if self.loading_angle >= 360:
                self.loading_angle = 0

            # Draw the loading text
            p.setPen(QtGui.QColor(255, 255, 255))
            p.setFont(QtGui.QFont("Arial", 20))
            p.drawText(self.pixmap.rect(), Qt.AlignCenter, self.loading_text)
            p.end()
            self.update()
            return

        # Draw groups
        if self.need_show_groups:
            pen = QtGui.QPen(QtGui.QColor("#AAAAAA"), 2, Qt.SolidLine)
            p.setPen(pen)
            grouped_shapes = {}
            for shape in self.shapes:
                if shape.group_id is None:
                    continue
                if shape.group_id not in grouped_shapes:
                    grouped_shapes[shape.group_id] = []
                grouped_shapes[shape.group_id].append(shape)

            for group_id in grouped_shapes:
                shapes = grouped_shapes[group_id]
                min_x = float("inf")
                min_y = float("inf")
                max_x = 0
                max_y = 0
                for shape in shapes:
                    rect = shape.bounding_rect()
                    if shape.shape_type == ShapeType.POINT:
                        points = shape.points[0]
                        min_x = min(min_x, points.x())
                        min_y = min(min_y, points.y())
                        max_x = max(max_x, points.x())
                        max_y = max(max_y, points.y())
                    else:
                        min_x = min(min_x, rect.x())
                        min_y = min(min_y, rect.y())
                        max_x = max(max_x, rect.x() + rect.width())
                        max_y = max(max_y, rect.y() + rect.height())
                    group_color = Constants.LABEL_COLOR_MAP[int(group_id) % len(Constants.LABEL_COLOR_MAP)]
                    pen.setStyle(Qt.SolidLine)
                    pen.setWidth(max(1, int(round(4.0 / Constants.SHAPE_SCALE))))
                    pen.setColor(QtGui.QColor(*group_color))
                    p.setPen(pen)

                    # Calculate the center point of the bounding rectangle
                    cx = rect.x() + rect.width() / 2
                    cy = rect.y() + rect.height() / 2
                    triangle_radius = max(1, int(round(3.0 / Constants.SHAPE_SCALE)))

                    # Define the points of the triangle
                    triangle_points = [
                        QtCore.QPointF(cx, cy - triangle_radius),
                        QtCore.QPointF(cx - triangle_radius, cy + triangle_radius),
                        QtCore.QPointF(cx + triangle_radius, cy + triangle_radius)
                    ]

                    # Draw the triangle
                    p.drawPolygon(QtGui.QPolygon(triangle_points))

                pen.setStyle(Qt.DashLine)
                pen.setWidth(max(1, int(round(1.0 / Constants.SHAPE_SCALE))))
                pen.setColor(QtGui.QColor("#EEEEEE"))
                p.setPen(pen)
                wrap_rect = QtCore.QRectF(min_x, min_y, max_x - min_x, max_y - min_y)
                p.drawRect(wrap_rect)

        # Draw KIE linking
        if self.need_show_linking:
            pen = QtGui.QPen(QtGui.QColor("#AAAAAA"), 2, Qt.SolidLine)
            p.setPen(pen)
            gid2point = {}
            linking_pairs = []
            group_color = (255, 128, 0)
            for shape in self.shapes:
                try:
                    linking_pairs += shape.kie_linking
                except Exception as e:
                    logger.warning(f"KIE linking join error: {e}. Shape = {shape}")

                if shape.group_id is None or shape.shape_type not in [ShapeType.RECTANGLE, ShapeType.POLYGON, ShapeType.ROTATION]:
                    continue
                rect = shape.get_bounding_rect()
                cx = rect.x() + (rect.width() / 2.0)
                cy = rect.y() + (rect.height() / 2.0)
                gid2point[shape.group_id] = (cx, cy)

            for linking in linking_pairs:
                pen.setStyle(Qt.SolidLine)
                pen.setWidth(max(1, int(round(4.0 / Constants.SHAPE_SCALE))))
                pen.setColor(QtGui.QColor(*group_color))
                p.setPen(pen)
                key, value = linking
                # Adapt to the 'ungroup_selected_shapes' operation
                if key not in gid2point or value not in gid2point:
                    continue
                kp, vp = gid2point[key], gid2point[value]
                # Draw a link from key point to value point
                p.drawLine(QtCore.QPointF(*kp), QtCore.QPointF(*vp))
                # Draw the triangle arrowhead
                arrow_size = max(1, int(round(10.0 / Constants.SHAPE_SCALE)))
                angle = math.atan2(vp[1] - kp[1], vp[0] - kp[0])
                arrow_points = [
                    QtCore.QPointF(vp[0], vp[1]),
                    QtCore.QPointF(vp[0] - arrow_size * math.cos(angle - math.pi / 6), vp[1] - arrow_size * math.sin(angle - math.pi / 6)),
                    QtCore.QPointF(vp[0] - arrow_size * math.cos(angle + math.pi / 6), vp[1] - arrow_size * math.sin(angle + math.pi / 6))
                ]
                p.drawPolygon(QtGui.QPolygon(arrow_points))

        # Draw degrees
        for shape in self.shapes:
            if (shape.is_selected or not self.is_hide_background) and self.visible_shapes.get(shape, True):
                shape.fill = self.is_fill_box and (shape.is_selected or shape == self.highlight_shape)
                shape.paint(p)
            if shape.shape_type == ShapeType.ROTATION and len(shape.points) == 4 and self.visible_shapes.get(shape, True):
                d = Constants.SHAPE_POINT_SIZE / Constants.SHAPE_SCALE
                center = QtCore.QPointF((shape.points[0].x() + shape.points[2].x()) / 2, (shape.points[0].y() + shape.points[2].y()) / 2)
                if self.need_show_degrees:
                    degrees = f"{int(math.degrees(shape.direction))}°"
                    p.setFont(QtGui.QFont("Arial", int(max(6.0, int(round(8.0 / Constants.SHAPE_SCALE))))))
                    pen = QtGui.QPen(QtGui.QColor("#FF9900"), 8, QtCore.Qt.SolidLine)
                    p.setPen(pen)
                    fm = QtGui.QFontMetrics(p.font())
                    rect = fm.boundingRect(degrees)
                    p.fillRect(
                        rect.x() + center.x() - d,
                        rect.y() + center.y() + d,
                        rect.width(),
                        rect.height(),
                        QtGui.QColor("#FF9900")
                    )
                    pen = QtGui.QPen(QtGui.QColor("#FFFFFF"), 7, QtCore.Qt.SolidLine)
                    p.setPen(pen)
                    p.drawText(center.x() - d, center.y() + d, degrees)
                else:
                    cp = QtGui.QPainterPath()
                    cp.addRect(center.x() - d / 2, center.y() - d / 2, d, d)
                    p.drawPath(cp)
                    p.fillPath(cp, QtGui.QColor(255, 153, 0, 255))

        if self.current:
            self.current.paint(p)
            self.line.paint(p)
        if self.selected_shapes_copy:
            for s in self.selected_shapes_copy:
                s.paint(p)

        if self.is_fill_box and self.create_mode == ShapeType.POLYGON and self.current is not None and len(self.current.points) >= 2:
            drawing_shape = self.current.copy()
            drawing_shape.add_point(self.line[1])
            drawing_shape.fill = True
            drawing_shape.paint(p)

        # Draw texts
        if self.need_show_texts:
            text_color = "#FFFFFF"
            background_color = "#007BFF"
            p.setFont(QtGui.QFont("Arial", int(max(6.0, int(round(8.0 / Constants.SHAPE_SCALE))))))
            pen = QtGui.QPen(QtGui.QColor(background_color), 8, Qt.SolidLine)
            p.setPen(pen)
            for shape in self.shapes:
                description = shape.description
                if description:
                    bbox = shape.get_bounding_rect()
                    fm = QtGui.QFontMetrics(p.font())
                    rect = fm.boundingRect(description)
                    p.fillRect(
                        int(rect.x() + bbox.x()),
                        int(rect.y() + bbox.y()),
                        int(rect.width()),
                        int(rect.height()),
                        QtGui.QColor(background_color),
                    )
                    p.drawText(int(bbox.x()), int(bbox.y()), description)
            pen = QtGui.QPen(QtGui.QColor(text_color), 8, Qt.SolidLine)
            p.setPen(pen)
            for shape in self.shapes:
                description = shape.description
                if description:
                    bbox = shape.get_bounding_rect()
                    p.drawText(int(bbox.x()), int(bbox.y()), description)

        # Draw labels
        if self.need_show_labels:
            p.setFont(QtGui.QFont("Arial", int(max(6.0, int(round(8.0 / Constants.SHAPE_SCALE))))))
            labels = []
            for shape in self.shapes:
                d_react = Constants.SHAPE_POINT_SIZE / Constants.SHAPE_SCALE
                d_text = 1.5
                if not shape.is_visible:
                    continue
                if shape.label in [AutoLabelEditMode.OBJECT.value, AutoLabelEditMode.ADD.value, AutoLabelEditMode.REMOVE.value]:
                    continue
                label_text = f"id: {shape.group_id if shape.group_id is not None else ''} {shape.label} {round(float(shape.score), 2) if shape.score is not None and self.need_show_scores else ''}"
                if not label_text:
                    continue
                fm = QtGui.QFontMetrics(p.font())
                bound_rect = fm.boundingRect(label_text)
                if shape.shape_type in [ShapeType.RECTANGLE, ShapeType.POLYGON, ShapeType.ROTATION]:
                    try:
                        bbox = shape.get_bounding_rect()
                    except IndexError:
                        continue
                    rect = QtCore.QRect(
                        int(bbox.x()),
                        int(bbox.y()),
                        int(bound_rect.width()),
                        int(bound_rect.height()),
                    )
                    text_pos = QtCore.QPoint(int(bbox.x()), int(bbox.y() + bound_rect.height() - d_text))
                elif shape.shape_type in [ShapeType.CIRCLE, ShapeType.LINE, ShapeType.LINE_STRIP, ShapeType.POINT]:
                    points = shape.points
                    point = points[0]
                    rect = QtCore.QRect(
                        int(point.x() + d_react),
                        int(point.y() - 15),
                        int(bound_rect.width()),
                        int(bound_rect.height()),
                    )
                    text_pos = QtCore.QPoint(int(point.x()), int(point.y() - 15 + bound_rect.height() - d_text))
                else:
                    continue
                labels.append((shape, rect, text_pos, label_text))

            pen = QtGui.QPen(QtGui.QColor("#FFA500"), 8, Qt.SolidLine)
            p.setPen(pen)
            for shape, rect, _, _ in labels:
                p.fillRect(rect, shape.line_color)

            pen = QtGui.QPen(QtGui.QColor("#FFFFFF"), 8, Qt.SolidLine)
            p.setPen(pen)
            for _, _, text_pos, label_text in labels:
                p.drawText(text_pos, label_text)

        # Draw mouse coordinates
        if self.need_show_cross_line:
            pen = QtGui.QPen(QtGui.QColor(self.cross_line.color), max(1, int(round(self.cross_line.width / Constants.SHAPE_SCALE))), Qt.DashLine)
            p.setPen(pen)
            p.setOpacity(self.cross_line.opacity)
            p.drawLine(QtCore.QPointF(self.prev_move_point.x(), 0), QtCore.QPointF(self.prev_move_point.x(), self.pixmap.height()))
            p.drawLine(QtCore.QPointF(0, self.prev_move_point.y()), QtCore.QPointF(self.pixmap.width(), self.prev_move_point.y()))

        p.end()
