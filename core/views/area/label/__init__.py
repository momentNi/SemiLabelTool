from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QScrollArea, QHBoxLayout, QComboBox

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
        self.auto_part = self.generate_auto_part()
        self.canvas_part = self.generate_canvas_part()

        self.layout.addWidget(self.instruction_part)
        self.layout.addWidget(self.auto_part)
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

    def generate_auto_part(self):
        auto_part = QWidget()
        auto_layout = QHBoxLayout()
        auto_layout.setAlignment(Qt.AlignLeft)
        auto_layout.setContentsMargins(0, 0, 0, 0)
        auto_layout.setSpacing(2)
        auto_layout.addWidget(QLabel("Select Model:"))

        model_select_combobox = QComboBox()
        model_select_combobox.setObjectName("model_select_combobox")
        model_select_combobox.setMinimumSize(200, 20)
        model_select_combobox.addItem("--- Select ---")
        auto_layout.addWidget(model_select_combobox)

        # TODO 根据不同的模型生成不同的operation panel
        operation_panel_dock = QtWidgets.QDockWidget("Operation Panel", self)
        operation_panel_dock.setHidden(True)
        operation_panel_dock.setFloating(True)
        operation_panel_dock.setStyleSheet(
            "QDockWidget::title {"
            "text-align: center;"
            "padding: 0px;"
            "background-color: #f0f0f0;"
            "}"
        )
        operation_panel_widget = QtWidgets.QWidget()
        operation_layout = QtWidgets.QGridLayout()

        operation_layout.addWidget(QLabel("Choose Output Shape Type:"))
        model_output_shape_combobox = QComboBox()
        model_output_shape_combobox.setObjectName("model_output_shape_combobox")
        model_output_shape_combobox.setMinimumSize(100, 20)
        model_output_shape_combobox.addItem("Polygon")
        model_output_shape_combobox.addItem("Rectangle")
        model_output_shape_combobox.addItem("Rotation")
        operation_layout.addWidget(model_output_shape_combobox)
        operation_layout.addWidget(QLabel("Choose Type of Target Area:"))

        operation_panel_widget.setLayout(operation_layout)
        operation_panel_dock.setWidget(operation_panel_widget)

        auto_part.setLayout(auto_layout)
        return auto_part

    @staticmethod
    def generate_canvas_part():
        scroll_area = QScrollArea()
        CORE.Object.scroll_area = scroll_area
        CORE.Object.canvas = Canvas()

        scroll_area.setWidget(CORE.Object.canvas)
        scroll_area.setWidgetResizable(True)

        return scroll_area
