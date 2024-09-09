from PyQt5.QtWidgets import QMenuBar

from core.views.area.menu.sub.file import FileMenu


class LabelMenuBar(QMenuBar):
    def __init__(self, parent=None):
        super(LabelMenuBar, self).__init__()
        self.parent = parent
        self.setObjectName("LabelMenuBar")
        self.menu_bar = QMenuBar(parent)
        self.menu_bar.addMenu(FileMenu("File", self.menu_bar).get_menu())

    def get_menu_bar(self):
        return self.menu_bar
