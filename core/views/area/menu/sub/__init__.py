import functools
from typing import final

from PyQt5.QtWidgets import QMenu, QMenuBar, QAction

from core.configs.core import CORE
from utils.logger import logger
from utils.qt_utils import create_new_action


class BaseMenu(QMenu):
    def __init__(self, name: str, parent: QMenuBar):
        super().__init__(name, parent)
        self.setObjectName(name)
        self.menu_action = functools.partial(create_new_action, self)
        self.action_dict = {}
        self.add_action_list_item()
        self.__add_actions()

    def add_action_list_item(self):
        raise NotImplementedError

    @final
    def __add_actions(self):
        if len(self.action_dict) == 0:
            logger.warning(f"{self.objectName()} Menu has no actions.")
        for name, widget in self.action_dict.items():
            setattr(CORE.Action, name, widget)
            if isinstance(widget, QAction):
                self.addAction(widget)
            elif isinstance(widget, QMenu):
                self.addMenu(widget)

    @final
    def get_menu(self):
        return self
