from core.configs.core import CORE
from core.services.actions.status import show_label_overview, show_box_settings, show_shape_overview, show_auto_label_overview
from core.views.area.menu.sub import BaseMenu


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
            "box_settings": self.menu_action(
                "Annotation box settings",
                show_box_settings,
                None,
                "edit",
                "Manage attributes of different annotation boxes",
                enabled=True
            ),
            "auto_label_overview": self.menu_action(
                "Auto Labeling Overview",
                show_auto_label_overview,
                None,
                "overview",
                "Show current status of auto labeling usage",
                enabled=True
            ),
            "d1": None,
            "reset_settings": self.menu_action(
                text=self.tr("Reset settings"),
                slot=lambda x: CORE.Variable.settings.set("reset", x),
                icon=None,
                tip=self.tr("Reset all settings value to initial value. (Needs to restart system to take effect)"),
                checkable=True,
                enabled=True,
                checked=CORE.Variable.settings.get("reset", False),
            )
        }
