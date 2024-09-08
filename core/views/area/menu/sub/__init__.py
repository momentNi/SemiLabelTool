import functools
from typing import final

from PyQt5.QtWidgets import QMenu, QMenuBar

from utils.qt_utils import create_new_action


class BaseMenu(QMenu):
    def __init__(self, name: str, parent: QMenuBar):
        super().__init__(name, parent)
        self.menu_action = functools.partial(create_new_action, self)
        self.add_actions()

    def add_actions(self):
        raise NotImplementedError

    @final
    def get_menu(self):
        return self
