from PyQt5.QtWidgets import QMainWindow, QStatusBar, QWidget, QHBoxLayout

from core.configs.constants import Constants
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

        self.setMenuBar(LabelMenuBar(self).get_menu_bar())

        base_layout = QHBoxLayout()
        base_layout.setContentsMargins(10, 10, 10, 10)

        self.left_widget = OperationArea(self)
        self.main_widget = LabelArea(self)
        self.right_widget = InformationArea(self)

        base_layout.addWidget(self.left_widget)
        base_layout.addWidget(self.main_widget)
        base_layout.addWidget(self.right_widget)
        widget = QWidget()
        widget.setLayout(base_layout)
        self.setCentralWidget(widget)

        status_bar = QStatusBar()
        status_bar.showMessage(f"{Constants.APP_NAME} - {Constants.APP_DESCRIPTION}")
        self.setStatusBar(status_bar)
