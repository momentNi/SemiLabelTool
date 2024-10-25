from PyQt5.QtWidgets import QMenuBar

from core.views.area.menu.sub.edit import EditMenu
from core.views.area.menu.sub.file import FileMenu
from core.views.area.menu.sub.view import ViewMenu


class LabelMenuBar(QMenuBar):
    def __init__(self, parent=None):
        super(LabelMenuBar, self).__init__()
        self.parent = parent
        self.setObjectName("LabelMenuBar")
        self.menu_bar = QMenuBar(parent)
        self.menu_bar.addMenu(FileMenu("File", self.menu_bar).get_menu())
        self.menu_bar.addMenu(EditMenu("Edit", self.menu_bar).get_menu())
        self.menu_bar.addMenu(ViewMenu("View", self.menu_bar).get_menu())

    def get_menu_bar(self):
        return self.menu_bar
