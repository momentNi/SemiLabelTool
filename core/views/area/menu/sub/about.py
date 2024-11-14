import webbrowser

from PyQt5 import QtWidgets

from core.configs.constants import Constants
from core.configs.core import CORE
from core.views.area.menu.sub import BaseMenu


class AboutMenu(BaseMenu):

    def __init__(self, name, parent):
        super().__init__(name, parent)
        self.parent = parent

    def add_action_list_item(self):
        self.action_dict = {
            "documents": self.menu_action(
                "Usage Documents",
                lambda: webbrowser.open("https://www.baidu.com"),
                "F1",
                "docs",
                "Show Usage Documents",
                enabled=True
            ),
            "author": self.menu_action(
                "About SemiLabelTool",
                lambda: QtWidgets.QMessageBox.information(
                    CORE.Object.main_window,
                    "About",
                    f"App name: {Constants.APP_NAME} \nVersion: {Constants.APP_VERSION} \nDevice: {Constants.DEVICE}"
                ),
                None,
                "help",
                "Show system information",
                enabled=True
            ),
        }
