from core.services.actions import file_actions
from core.views.area.menu.sub import BaseMenu


class FileMenu(BaseMenu):

    def __init__(self, name, parent):
        super().__init__(name, parent)
        self.parent = parent

    def add_actions(self):
        self.addAction(self.menu_action(
            "Open Image...",
            file_actions.open_file,
            "Ctrl+O",
            "file",
            "Open image or label file"
        ))
