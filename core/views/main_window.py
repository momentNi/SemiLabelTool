from PyQt5.QtWidgets import QMainWindow, QStatusBar, QWidget, QHBoxLayout, QVBoxLayout

import utils
from core.configs.constants import Constants
from core.configs.core import CORE
from core.services.system import set_item_description
from core.views.area.information import InformationArea
from core.views.area.label import LabelArea
from core.views.area.menu import LabelMenuBar
from core.views.area.operation import OperationArea


class MainWindow(QMainWindow):

    def __init__(self, app):
        super().__init__()
        self.app = app

        self.setContentsMargins(0, 0, 0, 0)
        self.setWindowTitle("SemiLabelTool")
        self.setObjectName("MainWindow")
        CORE.Object.main_window = self

        status_bar = QStatusBar()
        CORE.Object.status_bar = status_bar
        status_bar.showMessage(f"{Constants.APP_NAME} - {Constants.APP_DESCRIPTION}")
        self.setStatusBar(status_bar)

        base_layout = QHBoxLayout()
        base_layout.setContentsMargins(10, 10, 10, 10)

        self.left_widget = OperationArea(self)
        base_layout.addWidget(self.left_widget)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_widget = LabelArea(self)
        main_layout.addWidget(self.main_widget)
        base_layout.addItem(main_layout)
        base_layout.setStretch(1, 5)

        self.right_widget = InformationArea(self)
        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.addWidget(self.right_widget)
        base_layout.addItem(right_layout)
        base_layout.setStretch(2, 2)

        widget = QWidget()
        widget.setLayout(base_layout)
        self.setCentralWidget(widget)

        self.bind_actions()

    def bind_actions(self):
        # Menu Bar
        self.setMenuBar(LabelMenuBar(self).get_menu_bar())
        # Toolbar buttons
        self.left_widget.generate_tools()
        # Canvas
        CORE.Object.canvas.bind_signals()
        CORE.Object.canvas.init_menus()
        set_item_description(False)

    def closeEvent(self, event):
        if not utils.qt_utils.may_continue():
            event.ignore()
        CORE.Variable.settings.set("window/size", (self.size().width(), self.size().height()))
        CORE.Variable.settings.set("window/position", (self.pos().x(), self.pos().y()))
        CORE.Variable.settings.set("recent_files", CORE.Variable.recent_files)
        CORE.Variable.settings.set("filename", CORE.Variable.current_file_full_path if CORE.Variable.current_file_full_path else "")
        if CORE.Object.model_manager.model_dict is not None:
            models = {}
            for name, model_dto in CORE.Object.model_manager.model_dict.items():
                models[name] = {
                    "name": name,
                    "label": model_dto.label,
                    "platform": model_dto.platform,
                    "model_type": model_dto.model_type,
                    "config_path": model_dto.config_path
                }
            CORE.Variable.settings.set("models", models)

        print(CORE.Variable.settings.data)
        CORE.Variable.settings.save()
