from PyQt5 import QtWidgets, QtCore

from core.configs.core import CORE
from core.dto.enums import ShapeType, AutoLabelEditMode, AutoLabelShapeType
from core.models.model_manager import ModelManager
from core.services.system import show_critical_message, get_instruction_label
from core.views.dialogs.model_selection_dialog import ModelSelectionDialog
from utils.logger import logger


class SegmentationTab(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.model_dialog = None

        self.output_shape_type = QtWidgets.QComboBox()
        self.output_shape_type.addItem(ShapeType.POLYGON.name, ShapeType.POLYGON)
        self.output_shape_type.addItem(ShapeType.RECTANGLE.name, ShapeType.RECTANGLE)
        self.output_shape_type.addItem(ShapeType.ROTATION.name, ShapeType.ROTATION)
        self.output_shape_type.currentIndexChanged.connect(lambda: self.changed_value(True))

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
        self.add_point_button = QtWidgets.QPushButton("+ Point")
        self.add_point_button.setCheckable(True)
        self.remove_point_button = QtWidgets.QPushButton("- Point")
        self.remove_point_button.setCheckable(True)
        self.add_rect_button = QtWidgets.QPushButton("+ Rect")
        self.add_rect_button.setCheckable(True)
        self.remove_rect_button = QtWidgets.QPushButton("- Rect")
        self.remove_rect_button.setCheckable(True)
        self.add_point_button.clicked.connect(lambda: self.change_output_mode(1))
        self.remove_point_button.clicked.connect(lambda: self.change_output_mode(2))
        self.add_rect_button.clicked.connect(lambda: self.change_output_mode(3))
        self.remove_rect_button.clicked.connect(lambda: self.change_output_mode(4))

        self.clear_button = QtWidgets.QPushButton("Clear")
        self.clear_button.clicked.connect(lambda: self.change_output_mode(5))
        self.finish_button = QtWidgets.QPushButton("Finish Object")
        self.finish_button.clicked.connect(lambda: self.change_output_mode(6))
        op_layout.addWidget(self.add_point_button, 0, 0, 1, 1)
        op_layout.addWidget(self.remove_point_button, 1, 0, 1, 1)
        op_layout.addWidget(self.add_rect_button, 0, 1, 1, 1)
        op_layout.addWidget(self.remove_rect_button, 1, 1, 1, 1)
        op_layout.addWidget(self.clear_button, 2, 0, 1, 2)
        op_layout.addWidget(self.finish_button, 3, 0, 1, 2)
        self.op_widget.setLayout(op_layout)
        self.op_widget.setHidden(True)

        self.is_first_load = True

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
        self.changed_value(True)

    def update_total_weight(self):
        self.total_weight = 0.0
        for name, box in self.model_weight_value_spinbox:
            self.total_weight += box.value()
        self.total_label.setText(f"Total: {round(self.total_weight, 2)}")
        self.total_label.setStyleSheet(f"color: {'black' if round(self.total_weight, 2) == 1 else 'red'}")
        self.changed_value(True)

    def is_total_weight_valid(self):
        return round(self.total_weight, 2) == 1

    def changed_value(self, is_dirty: bool = True):
        self.save_button.setHidden(not is_dirty)
        self.op_widget.setHidden(is_dirty)

    def save_settings(self):
        if not self.is_total_weight_valid():
            show_critical_message("Error", "Total weight must be 1.0", trace=False)
            return

        CORE.Object.status_bar.showMessage("Saving Segmentation Model settings...")

        CORE.Object.canvas.set_auto_labeling_value(True)
        CORE.Object.instruction_part.setText(get_instruction_label())

        for name, box in self.model_weight_value_spinbox:
            CORE.Object.model_manager.active_models("seg", [name])
            # TODO set weight of each model
            logger.info(CORE.Object.model_manager.model_dict[name])
            CORE.Object.model_manager.model_dict[name].model.output_mode = self.output_shape_type.currentData()

        logger.info({
            "output_shape_type": self.output_shape_type.currentData(),
            "model_weight": [
                {
                    "name": name,
                    "value": box.value()
                } for name, box in self.model_weight_value_spinbox
            ]
        })
        self.changed_value(False)
        CORE.Object.status_bar.showMessage("Segmentation Model settings saved.")

    def change_output_mode(self, button_index: int):
        if button_index == 1:
            # + Point
            if self.add_point_button.isChecked():
                self.remove_point_button.setChecked(False)
                self.add_rect_button.setChecked(False)
                self.remove_rect_button.setChecked(False)
                CORE.Object.canvas.set_auto_labeling_mode(AutoLabelEditMode.ADD, AutoLabelShapeType.POINT)
            else:
                CORE.Object.canvas.set_auto_labeling_mode(AutoLabelEditMode.OFF, AutoLabelShapeType.OFF)
        elif button_index == 2:
            # - Point
            if self.remove_point_button.isChecked():
                self.add_point_button.setChecked(False)
                self.add_rect_button.setChecked(False)
                self.remove_rect_button.setChecked(False)
                CORE.Object.canvas.set_auto_labeling_mode(AutoLabelEditMode.REMOVE, AutoLabelShapeType.POINT)
            else:
                CORE.Object.canvas.set_auto_labeling_mode(AutoLabelEditMode.OFF, AutoLabelShapeType.OFF)
        elif button_index == 3:
            # + Rect
            if self.add_rect_button.isChecked():
                self.add_point_button.setChecked(False)
                self.remove_point_button.setChecked(False)
                self.remove_rect_button.setChecked(False)
                CORE.Object.canvas.set_auto_labeling_mode(AutoLabelEditMode.ADD, AutoLabelShapeType.RECTANGLE)
            else:
                CORE.Object.canvas.set_auto_labeling_mode(AutoLabelEditMode.OFF, AutoLabelShapeType.OFF)
        elif button_index == 4:
            # - Rect
            if self.remove_rect_button.isChecked():
                self.add_point_button.setChecked(False)
                self.remove_point_button.setChecked(False)
                self.add_rect_button.setChecked(False)
                CORE.Object.canvas.set_auto_labeling_mode(AutoLabelEditMode.REMOVE, AutoLabelShapeType.RECTANGLE)
            else:
                CORE.Object.canvas.set_auto_labeling_mode(AutoLabelEditMode.OFF, AutoLabelShapeType.OFF)
        elif button_index == 5:
            # Clear
            CORE.Object.canvas.clear_auto_labeling_marks()
        elif button_index == 6:
            # finish
            CORE.Object.canvas.finish_auto_labeling_object()
            self.clear_output_mode()

    def clear_output_mode(self):
        self.add_point_button.setChecked(False)
        self.remove_point_button.setChecked(False)
        self.add_rect_button.setChecked(False)
        self.remove_rect_button.setChecked(False)
        CORE.Object.canvas.set_auto_labeling_mode(AutoLabelEditMode.OFF, AutoLabelShapeType.OFF)
