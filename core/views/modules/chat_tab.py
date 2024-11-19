from PyQt5 import QtWidgets, QtCore

from core.services.signals.auto_labeling import send_chat_message
from core.views.modules.chat.chat_container import ChatContainer


class ChatTab(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        layout = QtWidgets.QVBoxLayout()
        self.chat_container = ChatContainer()
        layout.addWidget(self.chat_container)
        input_layout = QtWidgets.QHBoxLayout()
        self.message_input = QtWidgets.QTextEdit()
        self.message_input.setAcceptRichText(False)
        self.message_input.setPlaceholderText("Please input your labeling request...")
        self.message_input.setFocus()
        self.send_button = QtWidgets.QPushButton("Send")
        self.send_button.setDefault(True)
        self.send_button.setStyleSheet("height: 100%")
        self.send_button.clicked.connect(send_chat_message)
        input_layout.addWidget(self.message_input, 8)
        input_layout.addWidget(self.send_button, 0, QtCore.Qt.AlignBottom | QtCore.Qt.AlignRight)
        input_widget = QtWidgets.QWidget()
        input_widget.setLayout(input_layout)
        layout.addWidget(input_widget)
        layout.setStretch(0, 9)
        layout.setStretch(1, 1)
        self.setLayout(layout)
