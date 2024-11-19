from PyQt5 import QtWidgets, QtGui, QtCore

from core.dto.enums import MessageType
from core.views.modules.chat.avatar import Avatar, Triangle


class Bubble(QtWidgets.QLabel):
    def __init__(self, text, is_sender=False, parent=None):
        super(Bubble, self).__init__(text, parent)
        font = QtGui.QFont('MicrosoftYaHei', 12)
        self.setFont(font)
        self.setWordWrap(True)
        self.setMaximumWidth(800)
        self.setMinimumHeight(45)
        self.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        self.setSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Ignored)
        if is_sender:
            self.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignRight)
            self.setStyleSheet(
                '''
                background-color:#b2e281;
                border-radius:10px;
                padding:10px;
                '''
            )
        else:
            self.setStyleSheet(
                '''
                background-color:white;
                border-radius:10px;
                padding:10px;
                '''
            )
        font_metrics = QtGui.QFontMetrics(font)
        rect = font_metrics.boundingRect(text)
        self.setMaximumWidth(rect.width() + 30)

    def paintEvent(self, a0: QtGui.QPaintEvent) -> None:
        super(Bubble, self).paintEvent(a0)


class Message(QtWidgets.QWidget):
    def __init__(self, message_type, content, create_time):
        super(Message, self).__init__()
        self.loading_animation = QtGui.QMovie(":/images/images/loading.gif")
        self.loading = QtWidgets.QLabel(self)
        self.loading.setMovie(self.loading_animation)
        self.loading.resize(16, 16)
        self.loading.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)
        self.loading.setAutoFillBackground(False)

        self.message_type = message_type
        self.avatar = None
        self.triangle = None
        self.content = str(content)
        self.create_time = create_time

        if self.message_type == MessageType.USER:
            self.avatar = Avatar(":/images/images/user.png")
            self.triangle = Triangle(is_sender=True)
            self.content = Bubble(content, is_sender=True, parent=self)
            self.loading_animation.start()
            self.loading.show()
        elif self.message_type == MessageType.ROBOT:
            self.avatar = Avatar(":/images/images/robot.png")
            self.triangle = Triangle(is_sender=False)
            self.content = Bubble(content, is_sender=False, parent=self)

        self.is_sending = True

        self.init_ui()

    def init_ui(self):
        layout = QtWidgets.QHBoxLayout()
        layout.setSpacing(0)
        if self.message_type == MessageType.TIME:
            label = QtWidgets.QLabel(self.content)
            label.setMinimumSize(200, 30)
            label.setAlignment(QtCore.Qt.AlignCenter)
            label.setWordWrap(True)
            label.setStyleSheet("background-color: #DFE1E5;")
            label.adjustSize()
            layout.addWidget(label, 1, QtCore.Qt.AlignCenter)
        elif self.message_type == MessageType.USER:
            layout.addItem(QtWidgets.QSpacerItem(45 + 6, 45, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum))
            layout.addWidget(self.loading, 0, QtCore.Qt.AlignBottom | QtCore.Qt.AlignRight)
            layout.addWidget(self.content, 1)
            layout.addWidget(self.triangle, 0, QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft)
            layout.addWidget(self.avatar, 0, QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft)
        elif self.message_type == MessageType.ROBOT:
            layout.addWidget(self.avatar, 0, QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft)
            layout.addWidget(self.triangle, 0, QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft)
            layout.addWidget(self.content, 1)
            layout.addItem(QtWidgets.QSpacerItem(45 + 6, 45, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum))
        self.setLayout(layout)

    def set_success(self):
        self.is_sending = False
        self.loading.hide()
        self.loading_animation.stop()
        self.repaint()
