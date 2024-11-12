from core.dto.enums import ShapeType
from core.services.actions.edit import *
from core.views.area.menu.sub import BaseMenu


class EditMenu(BaseMenu):

    def __init__(self, name, parent):
        super().__init__(name, parent)
        self.parent = parent

    def add_action_list_item(self):
        self.action_dict = {
            "create_mode": self.menu_action(
                "Create Polygons",
                lambda: system.toggle_draw_mode(edit=False, create_mode=ShapeType.POLYGON),
                ["P", "Ctrl+N"],
                "polygon",
                "Start drawing polygons",
                enabled=False
            ),
            "create_rectangle_mode": self.menu_action(
                "Create Rectangle",
                lambda: system.toggle_draw_mode(edit=False, create_mode=ShapeType.RECTANGLE),
                ["R", "Ctrl+R"],
                "rectangle",
                "Start drawing rectangles",
                enabled=False
            ),
            "create_rotation_mode": self.menu_action(
                "Create Rotation",
                lambda: system.toggle_draw_mode(edit=False, create_mode=ShapeType.ROTATION),
                ["O"],
                "rotation",
                "Start drawing rotations",
                enabled=False
            ),
            "create_circle_mode": self.menu_action(
                "Create Circle",
                lambda: system.toggle_draw_mode(edit=False, create_mode=ShapeType.CIRCLE),
                [],
                "circle",
                "Start drawing circles",
                enabled=False
            ),
            "create_line_mode": self.menu_action(
                "Create Line",
                lambda: system.toggle_draw_mode(edit=False, create_mode=ShapeType.LINE),
                [],
                "line",
                "Start drawing lines",
                enabled=False
            ),
            "create_point_mode": self.menu_action(
                "Create Point",
                lambda: system.toggle_draw_mode(edit=False, create_mode=ShapeType.POINT),
                [],
                "point",
                "Start drawing points",
                enabled=False
            ),
            "create_line_strip_mode": self.menu_action(
                "Create LineStrip",
                lambda: system.toggle_draw_mode(edit=False, create_mode=ShapeType.LINE_STRIP),
                [],
                "line-strip",
                "Start drawing line strip. Ctrl + LeftClick ends creation",
                enabled=False
            ),
            "edit_object": self.menu_action(
                "Edit Object",
                system.set_edit_mode,
                "Ctrl+J",
                "edit",
                "Move and edit the selected polygons",
                enabled=False
            ),
            "edit_label": self.menu_action(
                "Edit Label",
                edit_label,
                "Ctrl+E",
                "edit",
                "Modify the label of the selected polygon",
                enabled=False
            ),
            "union_selection": self.menu_action(
                "Union Selection",
                union_selection,
                None,
                "union",
                "Union multiple selected rectangle shapes",
                enabled=False
            ),
            "duplicate_polygon": self.menu_action(
                "Duplicate Polygons",
                duplicate_selected_shape,
                "Ctrl+D",
                "copy",
                "Create a duplicate of the selected polygons",
                enabled=False
            ),
            "delete_polygon": self.menu_action(
                "Delete Polygons",
                delete_selected_shape,
                "Delete",
                "cancel",
                "Delete the selected polygons",
                enabled=False
            ),
            "copy_object": self.menu_action(
                "Copy Object",
                copy_selected_shape,
                "Ctrl+C",
                "copy",
                "Copy selected polygons to clipboard",
                enabled=False
            ),
            "paste_object": self.menu_action(
                "Paste Object",
                paste_selected_shape,
                "Ctrl+V",
                "paste",
                "Paste copied polygons",
                enabled=False
            ),
            "d1": None,
            "undo": self.menu_action(
                "Undo",
                undo_shape_edit,
                "Ctrl+Z",
                "undo",
                "Undo last add and edit of shape",
                enabled=False
            ),
            "undo_last_point": self.menu_action(
                "Undo last point",
                CORE.Object.canvas.undo_last_point,
                "Ctrl+Z",
                "undo",
                "Undo last drawn point",
                enabled=False
            ),
            "d2": None,
            "remove_selected_point": self.menu_action(
                "Remove Selected Point",
                remove_selected_point,
                "Backspace",
                "edit",
                "Remove selected point from polygon",
                enabled=False
            ),
            "d3": None,
            "keep_prev": self.menu_action(
                "Keep Previous Annotation",
                lambda x: CORE.Variable.settings.set("keep_prev", x),
                "Ctrl+P",
                None,
                'Toggle "Keep Previous Annotation" mode',
                checkable=True,
                checked=CORE.Variable.settings.get("keep_prev", False),
            ),
            "auto_use_last_label": self.menu_action(
                "Auto Use Last Label",
                lambda x: CORE.Variable.settings.set("auto_use_last_label", x),
                "Ctrl+Y",
                None,
                'Toggle "Auto Use Last Label" mode',
                checkable=True,
                checked=CORE.Variable.settings.get("auto_use_last_label", False),
            ),
            "shapes_visibility": self.menu_action(
                "Shapes Visibility",
                toggle_shapes_visibility,
                "Ctrl+H",
                None,
                'Toggle "Shapes Visibility" mode',
                checkable=True,
                checked=CORE.Variable.settings.get("show_shapes", True),
            )
        }
