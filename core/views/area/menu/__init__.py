from PyQt5.QtWidgets import QMenuBar

from core.views.area.menu.sub.about import AboutMenu
from core.views.area.menu.sub.edit import EditMenu
from core.views.area.menu.sub.file import FileMenu
from core.views.area.menu.sub.status import StatusMenu
from core.views.area.menu.sub.tools import ToolsMenu
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
        self.menu_bar.addMenu(ToolsMenu("Tools", self.menu_bar).get_menu())
        self.menu_bar.addMenu(StatusMenu("Status", self.menu_bar).get_menu())
        self.menu_bar.addMenu(AboutMenu("About", self.menu_bar).get_menu())

    def get_menu_bar(self):
        return self.menu_bar
