from core.configs.core import CORE
from core.services.actions.tools import save_crop_image
from core.views.area.menu.sub import BaseMenu


class ToolsMenu(BaseMenu):

    def __init__(self, name, parent):
        super().__init__(name, parent)
        self.parent = parent

    def add_action_list_item(self):
        self.action_dict = {
            "group_selected_shapes": self.menu_action(
                "Group Selected Shapes",
                CORE.Object.canvas.group_selected_shapes,
                "G",
                None,
                "Group shapes by assigning a same group id",
                enabled=True
            ),
            "ungroup_selected_shapes": self.menu_action(
                "Ungroup Selected Shapes",
                CORE.Object.canvas.ungroup_selected_shapes,
                "U",
                None,
                "Ungroup shapes",
                enabled=True
            ),
            "d1": None,
            "save_crop_image": self.menu_action(
                "Save Cropped Image",
                save_crop_image,
                None,
                "crop",
                "Save cropped image. (Support rectangle/rotation/polygon shape_type)",
                enabled=True
            )
        }
