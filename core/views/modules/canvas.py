from typing import List

from PyQt5 import QtGui, QtCore
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QWidget, QApplication

from core.configs.core import CORE
from core.dto.enums import ZoomMode
from utils.logger import logger


class Canvas(QWidget):
    def __init__(self, scroll_area):
        super().__init__()
        # 缩放模式 FIT_WINDOW, FIT_WIDTH, MANUAL_ZOOM = 0, 1, 2
        self.zoom_mode: ZoomMode = ZoomMode.FIT_WINDOW
        # 缩放比例 key=filename, value=(zoom_mode, zoom_value)
        self.zoom_values = {}
        self.scroll_area = scroll_area
        # 滚轮位置 key=filename, value=scroll_value
        self.scroll_values = {
            Qt.Horizontal: {},
            Qt.Vertical: {},
        }
        # 滚动条对象
        self.scroll_bars = {
            Qt.Vertical: scroll_area.verticalScrollBar(),
            Qt.Horizontal: scroll_area.horizontalScrollBar(),
        }
        # 当前画布中的对象
        self.shapes: List[str] = []

        self.scale = 1.0
        self._painter = QtGui.QPainter()
        self.pixmap = QPixmap()

    def is_no_shape(self):
        return len(self.shapes) == 0

    def set_scroll(self, orientation, value):
        self.scroll_bars[orientation].setValue(round(value))
        self.scroll_values[orientation][CORE.Variable.current_file_full_path] = value

    def load_pixmap(self, pixmap, clear_shapes=True):
        self.pixmap = pixmap
        if clear_shapes:
            self.shapes = []
        self.update()

    def reset_state(self):
        """Clear shapes and pixmap"""
        QApplication.restoreOverrideCursor()
        self.pixmap = None
        # self.shapes_backups = []
        self.update()

    @staticmethod
    def paint_canvas():
        if CORE.Variable.image.isNull():
            logger.error("cannot paint null image")
            return
        # CORE.Object.canvas.scale = 0.01 * self.zoom_widget.value()
        CORE.Object.canvas.adjustSize()
        CORE.Object.canvas.update()

    def offset_to_center(self):
        """Calculate offset to the center"""
        if self.pixmap is None:
            return QtCore.QPointF()
        s = self.scale
        area = super().size()
        w, h = self.pixmap.width() * s, self.pixmap.height() * s
        area_width, area_height = area.width(), area.height()
        x = (area_width - w) / (2 * s) if area_width > w else 0
        y = (area_height - h) / (2 * s) if area_height > h else 0
        return QtCore.QPointF(x, y)

    def paintEvent(self, event):  # noqa: C901
        """Paint event for canvas"""
        if self.pixmap is None or self.pixmap.width() == 0 or self.pixmap.height() == 0:
            super().paintEvent(event)
            return

        p = self._painter
        p.begin(self)
        p.setRenderHint(QtGui.QPainter.Antialiasing)
        p.setRenderHint(QtGui.QPainter.SmoothPixmapTransform)
        p.setRenderHint(QtGui.QPainter.HighQualityAntialiasing)

        p.scale(self.scale, self.scale)
        p.translate(self.offset_to_center())

        p.drawPixmap(0, 0, self.pixmap)
        # Shape.scale = self.scale
        #
        # # Draw loading/waiting screen
        # if self.is_loading:
        #     # Draw a semi-transparent rectangle
        #     p.setPen(Qt.NoPen)
        #     p.setBrush(QtGui.QColor(0, 0, 0, 20))
        #     p.drawRect(self.pixmap.rect())
        #
        #     # Draw a spinning wheel
        #     p.setPen(QtGui.QColor(255, 255, 255))
        #     p.setBrush(Qt.NoBrush)
        #     p.save()
        #     p.translate(self.pixmap.width() / 2, self.pixmap.height() / 2 - 50)
        #     p.rotate(self.loading_angle)
        #     p.drawEllipse(-20, -20, 40, 40)
        #     p.drawLine(0, 0, 0, -20)
        #     p.restore()
        #     self.loading_angle += 30
        #     if self.loading_angle >= 360:
        #         self.loading_angle = 0
        #
        #     # Draw the loading text
        #     p.setPen(QtGui.QColor(255, 255, 255))
        #     p.setFont(QtGui.QFont("Arial", 20))
        #     p.drawText(
        #         self.pixmap.rect(),
        #         Qt.AlignCenter,
        #         self.loading_text,
        #     )
        #     p.end()
        #     self.update()
        #     return
        #
        # # Draw groups
        # if self.show_groups:
        #     pen = QtGui.QPen(QtGui.QColor("#AAAAAA"), 2, Qt.SolidLine)
        #     p.setPen(pen)
        #     grouped_shapes = {}
        #     for shape in self.shapes:
        #         if shape.group_id is None:
        #             continue
        #         if shape.group_id not in grouped_shapes:
        #             grouped_shapes[shape.group_id] = []
        #         grouped_shapes[shape.group_id].append(shape)
        #
        #     for group_id in grouped_shapes:
        #         shapes = grouped_shapes[group_id]
        #         min_x = float("inf")
        #         min_y = float("inf")
        #         max_x = 0
        #         max_y = 0
        #         for shape in shapes:
        #             rect = shape.bounding_rect()
        #             if shape.shape_type == "point":
        #                 points = shape.points[0]
        #                 min_x = min(min_x, points.x())
        #                 min_y = min(min_y, points.y())
        #                 max_x = max(max_x, points.x())
        #                 max_y = max(max_y, points.y())
        #             else:
        #                 min_x = min(min_x, rect.x())
        #                 min_y = min(min_y, rect.y())
        #                 max_x = max(max_x, rect.x() + rect.width())
        #                 max_y = max(max_y, rect.y() + rect.height())
        #             group_color = LABEL_COLORMAP[
        #                 int(group_id) % len(LABEL_COLORMAP)
        #                 ]
        #             pen.setStyle(Qt.SolidLine)
        #             pen.setWidth(max(1, int(round(4.0 / Shape.scale))))
        #             pen.setColor(QtGui.QColor(*group_color))
        #             p.setPen(pen)
        #
        #             # Calculate the center point of the bounding rectangle
        #             cx = rect.x() + rect.width() / 2
        #             cy = rect.y() + rect.height() / 2
        #             triangle_radius = max(1, int(round(3.0 / Shape.scale)))
        #
        #             # Define the points of the triangle
        #             triangle_points = [
        #                 QtCore.QPointF(cx, cy - triangle_radius),
        #                 QtCore.QPointF(
        #                     cx - triangle_radius, cy + triangle_radius
        #                 ),
        #                 QtCore.QPointF(
        #                     cx + triangle_radius, cy + triangle_radius
        #                 ),
        #             ]
        #
        #             # Draw the triangle
        #             p.drawPolygon(triangle_points)
        #
        #         pen.setStyle(Qt.DashLine)
        #         pen.setWidth(max(1, int(round(1.0 / Shape.scale))))
        #         pen.setColor(QtGui.QColor("#EEEEEE"))
        #         p.setPen(pen)
        #         wrap_rect = QtCore.QRectF(
        #             min_x, min_y, max_x - min_x, max_y - min_y
        #         )
        #         p.drawRect(wrap_rect)
        #
        # # Draw KIE linking
        # if self.show_linking:
        #     pen = QtGui.QPen(QtGui.QColor("#AAAAAA"), 2, Qt.SolidLine)
        #     p.setPen(pen)
        #     gid2point = {}
        #     linking_pairs = []
        #     group_color = (255, 128, 0)
        #     for shape in self.shapes:
        #         try:
        #             linking_pairs += shape.kie_linking
        #         except:
        #             pass
        #
        #         if shape.group_id is None or shape.shape_type not in [
        #             "rectangle",
        #             "polygon",
        #             "rotation",
        #         ]:
        #             continue
        #         rect = shape.bounding_rect()
        #         cx = rect.x() + (rect.width() / 2.0)
        #         cy = rect.y() + (rect.height() / 2.0)
        #         gid2point[shape.group_id] = (cx, cy)
        #
        #     for linking in linking_pairs:
        #         pen.setStyle(Qt.SolidLine)
        #         pen.setWidth(max(1, int(round(4.0 / Shape.scale))))
        #         pen.setColor(QtGui.QColor(*group_color))
        #         p.setPen(pen)
        #         key, value = linking
        #         # Adapt to the 'ungroup_selected_shapes' operation
        #         if key not in gid2point or value not in gid2point:
        #             continue
        #         kp, vp = gid2point[key], gid2point[value]
        #         # Draw a link from key point to value point
        #         p.drawLine(QtCore.QPointF(*kp), QtCore.QPointF(*vp))
        #         # Draw the triangle arrowhead
        #         arrow_size = max(
        #             1, int(round(10.0 / Shape.scale))
        #         )  # Size of the arrowhead
        #         angle = math.atan2(
        #             vp[1] - kp[1], vp[0] - kp[0]
        #         )  # Angle towards the value point
        #         arrow_points = [
        #             QtCore.QPointF(vp[0], vp[1]),
        #             QtCore.QPointF(
        #                 vp[0] - arrow_size * math.cos(angle - math.pi / 6),
        #                 vp[1] - arrow_size * math.sin(angle - math.pi / 6),
        #                 ),
        #             QtCore.QPointF(
        #                 vp[0] - arrow_size * math.cos(angle + math.pi / 6),
        #                 vp[1] - arrow_size * math.sin(angle + math.pi / 6),
        #                 ),
        #         ]
        #         p.drawPolygon(arrow_points)
        #
        # # Draw degrees
        # for shape in self.shapes:
        #     if (
        #             shape.selected or not self._hide_backround
        #     ) and self.is_visible(shape):
        #         shape.fill = self._fill_drawing and (
        #                 shape.selected or shape == self.h_hape
        #         )
        #         shape.paint(p)
        #
        #     if (
        #             shape.shape_type == "rotation"
        #             and len(shape.points) == 4
        #             and self.is_visible(shape)
        #     ):
        #         d = shape.point_size / shape.scale
        #         center = QtCore.QPointF(
        #             (shape.points[0].x() + shape.points[2].x()) / 2,
        #             (shape.points[0].y() + shape.points[2].y()) / 2,
        #             )
        #         if self.show_degrees:
        #             degrees = str(int(math.degrees(shape.direction))) + "°"
        #             p.setFont(
        #                 QtGui.QFont(
        #                     "Arial",
        #                     int(max(6.0, int(round(8.0 / Shape.scale)))),
        #                 )
        #             )
        #             pen = QtGui.QPen(
        #                 QtGui.QColor("#FF9900"), 8, QtCore.Qt.SolidLine
        #             )
        #             p.setPen(pen)
        #             fm = QtGui.QFontMetrics(p.font())
        #             rect = fm.boundingRect(degrees)
        #             p.fillRect(
        #                 rect.x() + center.x() - d,
        #                 rect.y() + center.y() + d,
        #                 rect.width(),
        #                 rect.height(),
        #                 QtGui.QColor("#FF9900"),
        #                 )
        #             pen = QtGui.QPen(
        #                 QtGui.QColor("#FFFFFF"), 7, QtCore.Qt.SolidLine
        #             )
        #             p.setPen(pen)
        #             p.drawText(
        #                 center.x() - d,
        #                 center.y() + d,
        #                 degrees,
        #                 )
        #         else:
        #             cp = QtGui.QPainterPath()
        #             cp.addRect(
        #                 center.x() - d / 2,
        #                 center.y() - d / 2,
        #                 d,
        #                 d,
        #                 )
        #             p.drawPath(cp)
        #             p.fillPath(cp, QtGui.QColor(255, 153, 0, 255))
        #
        # if self.current:
        #     self.current.paint(p)
        #     self.line.paint(p)
        # if self.selected_shapes_copy:
        #     for s in self.selected_shapes_copy:
        #         s.paint(p)
        #
        # if (
        #         self.fill_drawing()
        #         and self.create_mode == "polygon"
        #         and self.current is not None
        #         and len(self.current.points) >= 2
        # ):
        #     drawing_shape = self.current.copy()
        #     drawing_shape.add_point(self.line[1])
        #     drawing_shape.fill = True
        #     drawing_shape.paint(p)
        #
        # # Draw texts
        # if self.show_texts:
        #     text_color = "#FFFFFF"
        #     background_color = "#007BFF"
        #     p.setFont(
        #         QtGui.QFont(
        #             "Arial", int(max(6.0, int(round(8.0 / Shape.scale))))
        #         )
        #     )
        #     pen = QtGui.QPen(QtGui.QColor(background_color), 8, Qt.SolidLine)
        #     p.setPen(pen)
        #     for shape in self.shapes:
        #         description = shape.description
        #         if description:
        #             bbox = shape.bounding_rect()
        #             fm = QtGui.QFontMetrics(p.font())
        #             rect = fm.boundingRect(description)
        #             p.fillRect(
        #                 int(rect.x() + bbox.x()),
        #                 int(rect.y() + bbox.y()),
        #                 int(rect.width()),
        #                 int(rect.height()),
        #                 QtGui.QColor(background_color),
        #             )
        #             p.drawText(
        #                 int(bbox.x()),
        #                 int(bbox.y()),
        #                 description,
        #             )
        #     pen = QtGui.QPen(QtGui.QColor(text_color), 8, Qt.SolidLine)
        #     p.setPen(pen)
        #     for shape in self.shapes:
        #         description = shape.description
        #         if description:
        #             bbox = shape.bounding_rect()
        #             p.drawText(
        #                 int(bbox.x()),
        #                 int(bbox.y()),
        #                 description,
        #             )
        #
        # # Draw labels
        # if self.show_labels:
        #     p.setFont(
        #         QtGui.QFont(
        #             "Arial", int(max(6.0, int(round(8.0 / Shape.scale))))
        #         )
        #     )
        #     labels = []
        #     for shape in self.shapes:
        #         d_react = shape.point_size / shape.scale
        #         d_text = 1.5
        #         if not shape.visible:
        #             continue
        #         if shape.label in [
        #             "AUTOLABEL_OBJECT",
        #             "AUTOLABEL_ADD",
        #             "AUTOLABEL_REMOVE",
        #         ]:
        #             continue
        #         label_text = (
        #                 (
        #                     f"id:{shape.group_id} "
        #                     if shape.group_id is not None
        #                     else ""
        #                 )
        #                 + (f"{shape.label}")
        #                 + (
        #                     f" {float(shape.score):.2f}"
        #                     if (shape.score is not None and self.show_scores)
        #                     else ""
        #                 )
        #         )
        #         if not label_text:
        #             continue
        #         fm = QtGui.QFontMetrics(p.font())
        #         bound_rect = fm.boundingRect(label_text)
        #         if shape.shape_type in ["rectangle", "polygon", "rotation"]:
        #             try:
        #                 bbox = shape.bounding_rect()
        #             except IndexError:
        #                 continue
        #             rect = QtCore.QRect(
        #                 int(bbox.x()),
        #                 int(bbox.y()),
        #                 int(bound_rect.width()),
        #                 int(bound_rect.height()),
        #             )
        #             text_pos = QtCore.QPoint(
        #                 int(bbox.x()),
        #                 int(bbox.y() + bound_rect.height() - d_text),
        #             )
        #         elif shape.shape_type in [
        #             "circle",
        #             "line",
        #             "linestrip",
        #             "point",
        #         ]:
        #             points = shape.points
        #             point = points[0]
        #             rect = QtCore.QRect(
        #                 int(point.x() + d_react),
        #                 int(point.y() - 15),
        #                 int(bound_rect.width()),
        #                 int(bound_rect.height()),
        #             )
        #             text_pos = QtCore.QPoint(
        #                 int(point.x()),
        #                 int(point.y() - 15 + bound_rect.height() - d_text),
        #             )
        #         else:
        #             continue
        #         labels.append((shape, rect, text_pos, label_text))
        #
        #     pen = QtGui.QPen(QtGui.QColor("#FFA500"), 8, Qt.SolidLine)
        #     p.setPen(pen)
        #     for shape, rect, _, _ in labels:
        #         p.fillRect(rect, shape.line_color)
        #
        #     pen = QtGui.QPen(QtGui.QColor("#FFFFFF"), 8, Qt.SolidLine)
        #     p.setPen(pen)
        #     for _, _, text_pos, label_text in labels:
        #         p.drawText(text_pos, label_text)
        #
        # # Draw mouse coordinates
        # if self.cross_line_show:
        #     pen = QtGui.QPen(
        #         QtGui.QColor(self.cross_line_color),
        #         max(1, int(round(self.cross_line_width / Shape.scale))),
        #         Qt.DashLine,
        #     )
        #     p.setPen(pen)
        #     p.setOpacity(self.cross_line_opacity)
        #     p.drawLine(
        #         QtCore.QPointF(self.prev_move_point.x(), 0),
        #         QtCore.QPointF(self.prev_move_point.x(), self.pixmap.height()),
        #     )
        #     p.drawLine(
        #         QtCore.QPointF(0, self.prev_move_point.y()),
        #         QtCore.QPointF(self.pixmap.width(), self.prev_move_point.y()),
        #     )

        p.end()
