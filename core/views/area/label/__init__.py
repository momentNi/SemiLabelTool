from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QScrollArea

from core.configs.core import CORE
from core.views.dialogs.label_dialog import LabelDialog
from core.views.modules.canvas import Canvas


class LabelArea(QWidget):
    def __init__(self, parent=None):
        super().__init__()
        self.parent = parent
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.mode = None

        self.canvas_part = self.generate_canvas_part()
        self.instruction_part = self.generate_instruction_part()
        self.auto_part = self.generate_auto_part()

        self.layout.addWidget(self.instruction_part)
        self.layout.addWidget(self.auto_part)
        self.layout.addWidget(self.canvas_part)
        self.setLayout(self.layout)

        CORE.Object.label_dialog = LabelDialog(
            labels=CORE.Variable.settings.get("labels", None),
            flags=CORE.Variable.settings.get("label_flags", None)
        )

    def generate_instruction_part(self):
        content = (
            f"<b>Mode:</b> {self.mode} | "
            f"<b>Shortcuts:</b>"
            f" Previous(<b>A</b>),"
            f" Next(<b>D</b>),"
            f" Rectangle(<b>R</b>),"
            f" Polygon(<b>P</b>),"
            f" Rotation(<b>O</b>)"
        )
        instruction_part = QLabel(content)
        instruction_part.setContentsMargins(0, 0, 0, 0)
        return instruction_part

    def generate_auto_part(self):
        auto_part = QWidget()
        # TODO Auto labeling part, rely on auto labeling module

        # Default tobe hide
        auto_part.hide()
        self.layout.addWidget(auto_part)
        return auto_part

    def generate_canvas_part(self):
        scroll_area = QScrollArea()
        CORE.Object.scroll_area = scroll_area
        CORE.Object.canvas = Canvas()
        self.mode = CORE.Object.canvas.get_canvas_mode()

        scroll_area.setWidget(CORE.Object.canvas)
        scroll_area.setWidgetResizable(True)

        return scroll_area
