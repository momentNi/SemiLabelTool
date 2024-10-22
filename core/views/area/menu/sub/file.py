from PyQt5.QtWidgets import QMenu

from core.configs.core import CORE
from core.services.actions import files as files_action
from core.views.area.menu.sub import BaseMenu


class FileMenu(BaseMenu):

    def __init__(self, name, parent):
        super().__init__(name, parent)
        self.parent = parent
        self.aboutToShow.connect(files_action.update_file_menu)

    def add_action_list_item(self):
        self.action_dict = {
            "open_image": self.menu_action(
                "Open Image...",
                files_action.open_file,
                "Ctrl+I",
                "file",
                "Open image or label file"
            ),
            "open_next_image": self.menu_action(
                "Next Image",
                files_action.open_next_image,
                ["D", "Ctrl+Shift+D"],
                "next",
                "Open next (hold Ctrl+Shift to move to the next labeled image)",
                enabled=False
            ),
            "open_prev_image": self.menu_action(
                "Previous Image",
                files_action.open_prev_image,
                ["A", "Ctrl+Shift+A"],
                "prev",
                "Open prev (hold Ctrl+Shift to move to the prev labeled image)",
                enabled=False
            ),
            "open_dir": self.menu_action(
                "Open Directory",
                files_action.open_directory,
                ["Ctrl+D"],
                "open",
                "Open Directory"
            ),
            "open_video": self.menu_action(
                "Open Video",
                files_action.open_video,
                ["Ctrl+Shift+V"],
                "video",
                "Open video file"
            ),
            "open_recent": QMenu("Open Recent"),
            "save_file": self.menu_action(
                "Save",
                files_action.save_file,
                ["Ctrl+S"],
                "save",
                "Save labels to file",
                enabled=False
            ),
            "save_file_as": self.menu_action(
                "Save as",
                files_action.save_file_as,
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
            "change_output_dir": self.menu_action(
                "Change Output Directory",
                slot=files_action.change_output_dir,
                icon="open",
                tip="Change where annotations are loaded/saved",
            ),
            "delete_file": self.menu_action(
                "Delete Label File",
                files_action.delete_label_file,
                ["Ctrl+Delete"],
                "delete",
                "Delete current label file",
                enabled=False
            ),
            "delete_image_file": self.menu_action(
                "Delete Image File",
                files_action.delete_image_file,
                ["Ctrl+Shift+Delete"],
                "delete",
                "Delete current image file",
                enabled=True
            ),
            "close": self.menu_action(
                "Close",
                files_action.close_file,
                ["Ctrl+Q"],
                "cancel",
                "Close current file",
            )
        }
