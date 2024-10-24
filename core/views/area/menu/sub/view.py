from core.configs.core import CORE
from core.services.actions import files as files_action
from core.views.area.menu.sub import BaseMenu


class ViewMenu(BaseMenu):

    def __init__(self, name, parent):
        super().__init__(name, parent)
        self.parent = parent

    def add_action_list_item(self):
        self.action_dict = {
            "flag_dock_toggle": CORE.Object.flag_dock.toggleViewAction(),
            "label_dock_toggle": CORE.Object.label_dock.toggleViewAction(),
            "shape_dock_toggle": CORE.Object.shape_dock.toggleViewAction(),
            "file_dock_toggle": CORE.Object.file_dock.toggleViewAction(),
            "s1": None,
            "fill_drawing_polygon": self.menu_action(
                "Open Image...",
                files_action.open_file,
                "Ctrl+I",
                "file",
                "Open image or label file"
            ),
            "s2": None,
            "s3": None,
            # "fit_width": self.menu_action(),
            # "fit_window": self.menu_action(),
        }
