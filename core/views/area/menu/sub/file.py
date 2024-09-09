from PyQt5.QtWidgets import QMenu

from core.configs.core import CORE
from core.services.actions import file_actions
from core.services.actions.file_actions import update_file_menu
from core.views.area.menu.sub import BaseMenu


class FileMenu(BaseMenu):

    def __init__(self, name, parent):
        super().__init__(name, parent)
        self.parent = parent
        self.aboutToShow.connect(update_file_menu)

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
                "Open next (hold Ctrl+Shift to move to the next labeled image)",
                enabled=False
            ),
            "open_prev_image": self.menu_action(
                "Previous Image",
                file_actions.open_prev_image,
                ["A", "Ctrl+Shift+A"],
                "prev",
                "Open prev (hold Ctrl+Shift to move to the prev labeled image)",
                enabled=False
            ),
            "open_dir": self.menu_action(
                "Open Directory",
                file_actions.open_directory,
                ["Ctrl+D"],
                "open",
                "Open Directory"
            ),
            "open_video": self.menu_action(
                "Open Video",
                file_actions.open_video,
                ["Ctrl+Shift+V"],
                "video",
                "Open video file"
            ),
            "open_recent": QMenu("Open Recent"),
            "save_file": self.menu_action(
                "Save",
                file_actions.save_file,
                ["Ctrl+S"],
                "save",
                "Save labels to file",
                enabled=False
            ),
            "save_file_as": self.menu_action(
                "Save as",
                file_actions.save_file_as,
                ["Ctrl+Shift+S"],
                "save-as",
                "Save labels to a different file",
                enabled=False
            ),
            "auto_save": self.menu_action(
                text="Save &Automatically",
                slot=lambda x: CORE.Variable.settings.set("auto_save", x),
                icon=None,
                tip="Save automatically",
                checkable=True,
                enabled=True,
                checked=CORE.Variable.settings.get("auto_save", False),
            ),
            "save_with_image_data": self.menu_action(
                text="Save With Image Data",
                slot=lambda x: CORE.Variable.settings.set("store_data", x),
                icon=None,
                tip="Save image data in label file",
                checkable=True,
                checked=CORE.Variable.settings.get("store_data", False),
            ),
        }
