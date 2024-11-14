from core.services.actions.status import show_label_overview, show_label_manager
from core.views.area.menu.sub import BaseMenu
from utils.logger import logger


class StatusMenu(BaseMenu):

    def __init__(self, name, parent):
        super().__init__(name, parent)
        self.parent = parent

    def add_action_list_item(self):
        self.action_dict = {
            "label_overview": self.menu_action(
                "Label Overview",
                show_label_overview,
                None,
                "overview",
                "Show overview statistics of all label annotations",
                enabled=True
            ),
            "shape_overview": self.menu_action(
                "Shape Overview",
                show_shape_overview,
                None,
                "overview",
                "Show overview statistics of all label shapes",
                enabled=True
            ),
            "label_manager": self.menu_action(
                "Label Manager",
                show_label_manager,
                None,
                "edit",
                "Manage attributes of all labels",
                enabled=True
            ),
            "d1": None,
            "object_detection_settings": self.menu_action(
                "Object Detection",
                lambda: logger.info("object_detection_settings"),
                None,
                "edit",
                "Object Detection Auto Labeling Settings",
                enabled=True
            ),
            "segmentation_settings": self.menu_action(
                "Semantic Segmentation",
                lambda: logger.info("segmentation_settings"),
                None,
                "edit",
                "Semantic Segmentation Auto Labeling Settings",
                enabled=True
            ),
            "gpt_settings": self.menu_action(
                "Natural Language",
                lambda: logger.info("gpt_settings"),
                None,
                "edit",
                "Natural Language Auto Labeling Settings",
                enabled=True
            ),
        }
