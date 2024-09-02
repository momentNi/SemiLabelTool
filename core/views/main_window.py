"""This module defines the main application window"""
from PyQt5.QtWidgets import QMainWindow, QStatusBar, QWidget, QHBoxLayout

from core import __appname__, __appdescription__
from core.views.modules.menu import LabelMenuBar


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
        # main_layout = QVBoxLayout()
        # main_layout.setContentsMargins(10, 10, 10, 10)
        # self.labeling_widget = LabelingWrapper(
        #     self,
        #     config=config,
        # )
        # main_layout.addWidget(self.labeling_widget)
        widget = QWidget()
        widget.setLayout(base_layout)
        # self.setCentralWidget(widget)

        status_bar = QStatusBar()
        status_bar.showMessage(f"{__appname__} - {__appdescription__}")
        self.setStatusBar(status_bar)
