import functools

from core.configs.core import CORE
from core.services.actions.canvas import add_zoom_value, set_zoom_value, set_fit_window, set_fit_width
from core.services.actions.views import set_brightness_contrast, set_cross_line, hide_selected_polygons, show_hidden_polygons
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
            "d1": None,
            "fill_drawing_polygon": self.menu_action(
                "Fill Drawing Polygon",
                lambda x: setattr(CORE.Object.canvas, "is_fill_box", x),
                None,
                None,
                "Fill polygon while drawing",
                checkable=True,
                checked=CORE.Variable.settings.get("fill_box", True),
                enabled=True
            ),
            "d2": None,
            "zoom_in": self.menu_action(
                "Zoom In",
                lambda: functools.partial(add_zoom_value, 1.1),
                "Ctrl++",
                "zoom-in",
                "Increase zoom level",
                enabled=False
            ),
            "zoom_out": self.menu_action(
                "Zoom In",
                lambda: functools.partial(add_zoom_value, 0.9),
                "Ctrl+-",
                "zoom-out",
                "Decrease zoom level",
                enabled=False
            ),
            "zoom_original": self.menu_action(
                "Zoom In",
                lambda: functools.partial(set_zoom_value, 100),
                "Ctrl+0",
                "zoom",
                "Zoom to original size",
                enabled=False
            ),
            "keep_prev_scale": self.menu_action(
                "Keep Previous Scale",
                lambda x: CORE.Variable.settings.set("keep_prev_scale", x),
                None,
                None,
                "Keep previous zoom scale",
                checkable=True,
                checked=CORE.Variable.settings.get("keep_prev_scale", False),
                enabled=True
            ),
            "keep_prev_brightness": self.menu_action(
                "Keep Previous Brightness",
                lambda x: CORE.Variable.settings.set("keep_prev_brightness", x),
                None,
                None,
                "Keep previous brightness",
                checkable=True,
                checked=CORE.Variable.settings.get("keep_prev_brightness", False),
                enabled=True
            ),
            "keep_prev_contrast": self.menu_action(
                "Keep Previous Contrast",
                lambda x: CORE.Variable.settings.set("keep_prev_contrast", x),
                None,
                None,
                "Keep previous contrast",
                checkable=True,
                checked=CORE.Variable.settings.get("keep_prev_contrast", False),
                enabled=True
            ),
            "d3": None,
            "fit_window": self.menu_action(
                "Fit Window",
                set_fit_window,
                "Ctrl+F",
                "fit-window",
                "Zoom follows window size",
                checkable=True,
                enabled=False
            ),
            "fit_width": self.menu_action(
                "Fit Width",
                set_fit_width,
                "Ctrl+Shift+F",
                "fit-width",
                "Zoom follows window width",
                checkable=True,
                enabled=False
            ),
            "d4": None,
            "set_brightness_contrast": self.menu_action(
                "Set Brightness Contrast",
                set_brightness_contrast,
                None,
                "color",
                "Adjust brightness and contrast",
                enabled=False
            ),
            "set_cross_line": self.menu_action(
                "Set Cross Line",
                set_cross_line,
                None,
                "cartesian",
                "Set cross line for mouse position"
            ),
            "show_description": self.menu_action(
                "Show Description",
                lambda x: setattr(CORE.Object.canvas, "need_show_description", x),
                "Ctrl+T",
                None,
                "Show description above shapes",
                checkable=True,
                checked=CORE.Variable.settings.get("need_show_description", True),
                enabled=True,
                auto_trigger=True,
            ),
            "show_labels": self.menu_action(
                "Show Labels",
                lambda x: setattr(CORE.Object.canvas, "need_show_labels", x),
                "Ctrl+L",
                None,
                "Show label inside shapes",
                checkable=True,
                checked=CORE.Variable.settings.get("need_show_labels", True),
                enabled=True,
                auto_trigger=True,
            ),
            "show_scores": self.menu_action(
                "Show Scores",
                lambda x: setattr(CORE.Object.canvas, "need_show_scores", x),
                None,
                None,
                "Show score inside shapes",
                checkable=True,
                checked=CORE.Variable.settings.get("need_show_scores", True),
                enabled=True,
                auto_trigger=True,
            ),
            "show_degrees": self.menu_action(
                "Show Degrees",
                lambda x: setattr(CORE.Object.canvas, "need_show_degrees", x),
                None,
                None,
                "Show degrees above rotated shapes",
                checkable=True,
                checked=CORE.Variable.settings.get("need_show_degrees", True),
                enabled=True,
                auto_trigger=True,
            ),
            "show_kie_linking": self.menu_action(
                "Show KIE Linking",
                lambda x: setattr(CORE.Object.canvas, "need_show_linking", x),
                "Ctrl+K",
                None,
                "Show KIE linking between key and value",
                checkable=True,
                checked=CORE.Variable.settings.get("need_show_linking", True),
                enabled=True,
                auto_trigger=True,
            ),
            "show_groups": self.menu_action(
                "Show Groups",
                lambda x: setattr(CORE.Object.canvas, "need_show_groups", x),
                None,
                None,
                "Show shape groups",
                checkable=True,
                checked=CORE.Variable.settings.get("need_show_groups", True),
                enabled=True,
                auto_trigger=True,
            ),
            "hide_selected_polygons": self.menu_action(
                "Hide Selected Polygons",
                hide_selected_polygons,
                "S",
                None,
                "Hide selected polygons",
                enabled=True,
            ),
            "show_hidden_polygons": self.menu_action(
                "Show Hidden Polygons",
                show_hidden_polygons,
                "W",
                None,
                "Show hidden polygons",
                enabled=True,
            ),
        }
