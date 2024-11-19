from PyQt5 import QtWidgets, QtGui, QtCore


class Avatar(QtWidgets.QLabel):
    def __init__(self, avatar, parent=None):
        super().__init__(parent)
        if isinstance(avatar, str):
            self.setPixmap(QtGui.QPixmap(avatar).scaled(45, 45))
            self.image_path = avatar
        elif isinstance(avatar, QtGui.QPixmap):
            self.setPixmap(avatar.scaled(45, 45))
        self.setFixedSize(QtCore.QSize(45, 45))


class Triangle(QtWidgets.QLabel):
    def __init__(self, is_sender=False, parent=None):
        super().__init__(parent)
        self.is_sender = is_sender
        self.setFixedSize(6, 45)

    def paintEvent(self, a0: QtGui.QPaintEvent) -> None:
        super(Triangle, self).paintEvent(a0)
        painter = QtGui.QPainter(self)
        triangle = QtGui.QPolygon()
        if self.is_sender:
            painter.setPen(QtGui.QColor('#b2e281'))
            painter.setBrush(QtGui.QColor('#b2e281'))
            triangle.setPoints(0, 10, 0, 30, 6, 20)
        else:
            painter.setPen(QtGui.QColor('white'))
            painter.setBrush(QtGui.QColor('white'))
            triangle.setPoints(0, 20, 6, 10, 6, 30)
        painter.drawPolygon(triangle)
