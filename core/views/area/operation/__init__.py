from PyQt5 import QtCore
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout

from core.views.area.operation.tools import ToolBar


class OperationArea(QWidget):
    def __init__(self, parent=None):
        super().__init__()
        self.parent = parent
        self.toolbar = ToolBar("ToolBar")

        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.toolbar.setObjectName("ToolBar")
        self.toolbar.setOrientation(Qt.Vertical)
        self.toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        self.toolbar.setIconSize(QtCore.QSize(24, 24))
        self.toolbar.setMaximumWidth(40)
        self.layout.addWidget(self.toolbar)

        self.setLayout(self.layout)

    def generate_tools(self):
        self.toolbar.generate_zoom_widget()
        self.toolbar.generate_actions()
