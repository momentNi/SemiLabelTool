import time
from typing import Dict, Optional

from PyQt5 import QtWidgets, QtCore

from core.dto.enums import MessageType
from core.views.modules.chat.message import Message


class ScrollAreaContent(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.adjustSize()


class ChatContainer(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.messages: Dict[int, Message] = {}
        self.last_message_time: Optional[int] = None
        self.spacer = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)

        layout = QtWidgets.QVBoxLayout()
        layout.setSpacing(0)
        self.container = QtWidgets.QScrollArea()
        self.container.setWidgetResizable(True)
        self.container.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.container.setStyleSheet("border:none")
        self.message_area = ScrollAreaContent()
        self.container.setWidget(self.message_area)
        layout.addWidget(self.container)

        self.message_area_layout = QtWidgets.QVBoxLayout()
        self.message_area_layout.setSpacing(0)
        self.message_area.setLayout(self.message_area_layout)
        self.scroll_bottom_flag = False
        self.container.verticalScrollBar().rangeChanged.connect(self.scroll_bottom)
        self.setLayout(layout)

    def add_message(self, message: Message):
        self.message_area_layout.removeItem(self.spacer)
        current_time = time.localtime()
        current_time_int = int(time.mktime(current_time))
        if self.last_message_time is None or current_time_int - self.last_message_time > 60:
            self.message_area_layout.addWidget(Message(MessageType.TIME, time.strftime("%Y-%m-%d %H:%M", current_time), current_time_int))
        self.message_area_layout.addWidget(message)
        self.message_area_layout.addSpacerItem(self.spacer)
        self.messages[current_time_int] = message
        if self.last_message_time is not None and getattr(self.messages.get(self.last_message_time), "message_type", None) == MessageType.USER:
            self.messages[self.last_message_time].set_success()
        self.last_message_time = current_time_int
        self.scroll_bottom_flag = True

    def update(self) -> None:
        super().update()
        self.message_area.adjustSize()
        self.container.update()

    def scroll_bottom(self):
        if self.scroll_bottom_flag:
            self.container.verticalScrollBar().setValue(self.container.verticalScrollBar().maximum())
            self.scroll_bottom_flag = False
