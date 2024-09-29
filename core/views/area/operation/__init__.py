from PyQt5 import QtCore
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout

from core.views.area.operation.tools import ToolBar


class OperationArea(QWidget):
    def __init__(self, parent=None):
        super().__init__()
        self.parent = parent
        self.layout = QVBoxLayout()
        self.generate_content()
        self.setLayout(self.layout)

    def generate_content(self):
        toolbar = ToolBar("ToolBar")
        toolbar.setObjectName("ToolBar")
        toolbar.setOrientation(Qt.Vertical)
        # toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        toolbar.setIconSize(QtCore.QSize(24, 24))
        toolbar.setMaximumWidth(40)
        self.layout.addWidget(toolbar)
