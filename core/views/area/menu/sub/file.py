from core.services.actions import file_actions
from core.views.area.menu.sub import BaseMenu


class FileMenu(BaseMenu):

    def __init__(self, name, parent):
        super().__init__(name, parent)
        self.parent = parent

    def add_action_list_item(self):
        self.action_dict = {
            "open_image": self.menu_action(
                "Open Image...",
                file_actions.open_file,
                "Ctrl+I",
                "file",
                "Open image or label file"
            ),
            "open_next_image": self.menu_action(
                "Next Image",
                file_actions.open_next_image,
                ["D", "Ctrl+Shift+D"],
                "next",
                "Open next (hold Ctrl+Shift to move to the next labeled image)"
            ),
            "open_prev_image": self.menu_action(
                "Previous Image",
                file_actions.open_prev_image,
                ["A", "Ctrl+Shift+A"],
                "prev",
                "Open prev (hold Ctrl+Shift to move to the prev labeled image)"
            ),
            "open_dir": self.menu_action(
                "Open Directory",
                file_actions.open_directory,
                ["Ctrl+D"],
                "open",
                "Open Directory"
            )
        }
