from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QScrollArea

from core.configs.core import CORE
from core.services.system import get_instruction_label
from core.views.dialogs.label_dialog import LabelDialog
from core.views.modules.canvas import Canvas


class LabelArea(QWidget):
    def __init__(self, parent=None):
        super().__init__()
        self.parent = parent
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.instruction_part = self.generate_instruction_part()
        CORE.Object.instruction_part = self.instruction_part
        self.canvas_part = self.generate_canvas_part()

        self.layout.addWidget(self.instruction_part)
        self.layout.addWidget(self.canvas_part)
        self.setLayout(self.layout)

        CORE.Object.label_dialog = LabelDialog(
            labels=CORE.Variable.settings.get("labels", None),
            flags=CORE.Variable.settings.get("label_flags", None)
        )

    @staticmethod
    def generate_instruction_part():
        instruction_part = QLabel(get_instruction_label())
        instruction_part.setContentsMargins(0, 0, 0, 0)
        return instruction_part

    @staticmethod
    def generate_canvas_part():
        scroll_area = QScrollArea()
        CORE.Object.scroll_area = scroll_area
        CORE.Object.canvas = Canvas()

        scroll_area.setWidget(CORE.Object.canvas)
        scroll_area.setWidgetResizable(True)

        return scroll_area
