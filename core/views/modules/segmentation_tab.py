from PyQt5 import QtWidgets, QtCore

from core.configs.core import CORE
from core.dto.enums import ShapeType
from core.models.model_manager import ModelManager
from core.services.system import show_critical_message
from core.views.dialogs.model_selection_dialog import ModelSelectionDialog


class SegmentationTab(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.model_dialog = None

        self.output_shape_type = QtWidgets.QComboBox()
        self.output_shape_type.addItem(ShapeType.POLYGON.name, ShapeType.POLYGON.value)
        self.output_shape_type.addItem(ShapeType.RECTANGLE.name, ShapeType.RECTANGLE.value)
        self.output_shape_type.addItem(ShapeType.ROTATION.name, ShapeType.ROTATION.value)
        self.output_shape_type.currentIndexChanged.connect(lambda: setattr(self, "is_modified", True) or self.change_buttons())

        self.container = QtWidgets.QScrollArea()
        self.container.setMaximumHeight(400)
        self.container.setWidgetResizable(True)
        self.container.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.container.setStyleSheet("border:none")
        self.total_weight = 1.00
        self.total_label = QtWidgets.QLabel()
        self.total_label.setAlignment(QtCore.Qt.AlignRight)
        self.model_weight_value_spinbox = []

        self.save_button = QtWidgets.QPushButton("Save")
        self.save_button.clicked.connect(self.save_settings)
        self.save_button.setHidden(True)

        self.op_widget = QtWidgets.QWidget()
        op_layout = QtWidgets.QGridLayout()
        add_point_button = QtWidgets.QPushButton("+ Point")
        remove_point_button = QtWidgets.QPushButton("- Point")
        add_rect_button = QtWidgets.QPushButton("+ Rect")
        remove_rect_button = QtWidgets.QPushButton("- Rect")
        clear_button = QtWidgets.QPushButton("Clear")
        finish_button = QtWidgets.QPushButton("Finish Object")
        op_layout.addWidget(add_point_button, 0, 0, 1, 1)
        op_layout.addWidget(remove_point_button, 1, 0, 1, 1)
        op_layout.addWidget(add_rect_button, 0, 1, 1, 1)
        op_layout.addWidget(remove_rect_button, 1, 1, 1, 1)
        op_layout.addWidget(clear_button, 2, 0, 1, 2)
        op_layout.addWidget(finish_button, 3, 0, 1, 2)
        self.op_widget.setLayout(op_layout)
        self.op_widget.setHidden(True)

        self.is_first_load = True
        self.is_modified = True

        layout = QtWidgets.QVBoxLayout()
        self.model_layout = QtWidgets.QFormLayout()
        self.model_layout.setLabelAlignment(QtCore.Qt.AlignRight)
        self.model_layout.setHorizontalSpacing(20)
        self.model_layout.setVerticalSpacing(15)
        self.select_model_button = QtWidgets.QPushButton("Select...")
        self.select_model_button.clicked.connect(self.select_model)
        self.model_layout.addRow("Select Models", self.select_model_button)
        layout.addLayout(self.model_layout)

        self.setLayout(layout)

    def select_model(self):
        if CORE.Object.model_manager is None:
            CORE.Object.model_manager = ModelManager()
        if self.model_dialog is None:
            self.model_dialog = ModelSelectionDialog()
            self.model_dialog.load_default_models(CORE.Object.model_manager.seg_models)
        result = self.model_dialog.exec_()
        if result == QtWidgets.QDialog.Accepted:
            selected_models = [self.model_dialog.right_list_widget.item(i).text() for i in range(self.model_dialog.right_list_widget.count())]
            self.update_model_weight_box(selected_models)
            self.is_first_load = False

    def update_model_weight_box(self, selected_models):
        if self.is_first_load:
            self.model_layout.addRow("Output Shape Type", self.output_shape_type)
            self.update_weight_container(selected_models)
            self.model_layout.addRow("Result Weight", self.container)
            self.model_layout.addRow("", self.total_label)
            self.layout().addWidget(self.save_button)
            self.layout().addWidget(self.op_widget)
        else:
            self.update_weight_container(selected_models)
        self.is_modified = True
        self.change_buttons()

    def update_weight_container(self, selected_models):
        weight_box_widget = QtWidgets.QWidget()
        weight_box_widget.adjustSize()
        self.container.setWidget(weight_box_widget)

        weight_box_layout = QtWidgets.QFormLayout()
        if len(selected_models) > 0:
            # update model weight box based on selected model
            weight_sum = 0
            # in case of indivisibility, add a single weight to the last model
            self.model_weight_value_spinbox = [(model, QtWidgets.QDoubleSpinBox()) for model in selected_models]
            for i in range(len(selected_models)):
                self.model_weight_value_spinbox[i][1].setSingleStep(0.01)
                value = round(1 / len(selected_models), 2)
                self.model_weight_value_spinbox[i][1].setValue(value)
                self.model_weight_value_spinbox[i][1].valueChanged.connect(self.update_total_weight)
                weight_sum += value
            self.model_weight_value_spinbox[-1][1].setValue(self.model_weight_value_spinbox[-1][1].value() + 1 - weight_sum)
            self.update_total_weight()
            for i in range(len(selected_models)):
                weight_box_layout.addRow(selected_models[i], self.model_weight_value_spinbox[i][1])
        weight_box_widget.setLayout(weight_box_layout)

    def update_total_weight(self):
        self.total_weight = 0.0
        for name, box in self.model_weight_value_spinbox:
            self.total_weight += box.value()
        self.total_label.setText(f"Total: {round(self.total_weight, 2)}")
        self.total_label.setStyleSheet(f"color: {'black' if round(self.total_weight, 2) == 1 else 'red'}")
        self.is_modified = True
        self.change_buttons()

    def is_total_weight_valid(self):
        return round(self.total_weight, 2) == 1

    def change_buttons(self):
        self.save_button.setHidden(not self.is_modified)
        self.op_widget.setHidden(self.is_modified)

    def save_settings(self):
        if not self.is_total_weight_valid():
            show_critical_message("Error", "Total weight must be 1.0", trace=False)
            return
        # TODO
        print({
            "output_shape_type": self.output_shape_type.currentData(),
            "model_weight": [
                {
                    "name": name,
                    "value": box.value()
                } for name, box in self.model_weight_value_spinbox
            ]
        })
        self.is_modified = False
        self.change_buttons()
