from PyQt5.QtWidgets import QMainWindow, QStatusBar, QWidget, QHBoxLayout, QVBoxLayout

from core.configs.constants import Constants
from core.configs.core import CORE
from core.views.area.information import InformationArea
from core.views.area.label import LabelArea
from core.views.area.menu import LabelMenuBar
from core.views.area.operation import OperationArea


class MainWindow(QMainWindow):

    def __init__(self, app, config):
        super().__init__()
        self.app = app
        self.config = config

        self.setContentsMargins(0, 0, 0, 0)
        self.setWindowTitle("SemiLabelTool")
        self.setObjectName("MainWindow")
        CORE.Object.main_window = self

        base_layout = QHBoxLayout()
        base_layout.setContentsMargins(10, 10, 10, 10)

        self.left_widget = OperationArea(self)

        self.main_widget = LabelArea(self)
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.main_widget)

        self.right_widget = InformationArea(self)
        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.addWidget(self.right_widget)

        base_layout.addWidget(self.left_widget)
        base_layout.addItem(main_layout)
        base_layout.setStretch(1, 1)
        base_layout.addItem(right_layout)
        widget = QWidget()
        widget.setLayout(base_layout)
        self.setCentralWidget(widget)

        self.setMenuBar(LabelMenuBar(self).get_menu_bar())

        status_bar = QStatusBar()
        CORE.Object.status_bar = status_bar
        status_bar.showMessage(f"{Constants.APP_NAME} - {Constants.APP_DESCRIPTION}")
        self.setStatusBar(status_bar)
