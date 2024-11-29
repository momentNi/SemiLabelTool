from PyQt5 import QtWidgets, QtCore

from core.configs.core import CORE
from core.dto.enums import ShapeType
from core.models.model_manager import ModelManager
from core.services.system import show_critical_message
from core.views.dialogs.model_selection_dialog import ModelSelectionDialog
from utils.logger import logger


class ObjectDetectionTab(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.output_shape_type = QtWidgets.QComboBox()
        self.output_shape_type.addItem(ShapeType.RECTANGLE.name, ShapeType.RECTANGLE.value)
        self.output_shape_type.addItem(ShapeType.POINT.name, ShapeType.POINT.value)
        self.output_shape_type.addItem(ShapeType.POLYGON.name, ShapeType.POLYGON.value)
        self.output_shape_type.currentIndexChanged.connect(lambda: self.changed_value(True))
        self.conf_threshold = QtWidgets.QDoubleSpinBox()
        self.conf_threshold.setSingleStep(0.01)
        self.conf_threshold.setMaximum(1)
        self.conf_threshold.setMinimum(0)
        self.conf_threshold.valueChanged.connect(lambda: self.changed_value(True))
        self.iou_threshold = QtWidgets.QDoubleSpinBox()
        self.iou_threshold.setSingleStep(0.01)
        self.iou_threshold.setMaximum(1)
        self.iou_threshold.setMinimum(0)
        self.iou_threshold.valueChanged.connect(lambda: self.changed_value(True))
        self.container = QtWidgets.QScrollArea()
        self.container.setMaximumHeight(400)
        self.container.setWidgetResizable(True)
        self.container.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.container.setStyleSheet("border:none")
        self.total_label = QtWidgets.QLabel()
        self.total_label.setAlignment(QtCore.Qt.AlignRight)
        self.save_button = QtWidgets.QPushButton("Save")
        self.apply_current_button = QtWidgets.QPushButton("Apply Current")
        self.apply_all_button = QtWidgets.QPushButton("Apply All")
        self.model_weight_value_spinbox = []
        self.total_weight = 1.00
        self.is_preserve = True
        self.is_first_load = True
        self.model_dialog = None

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
            self.model_dialog.load_default_models(CORE.Object.model_manager.od_models)
        result = self.model_dialog.exec_()
        if result == QtWidgets.QDialog.Accepted:
            selected_models = [self.model_dialog.right_list_widget.item(i).text() for i in range(self.model_dialog.right_list_widget.count())]
            self.update_model_weight_box(selected_models)
            self.is_first_load = False

    def update_model_weight_box(self, selected_models):
        if self.is_first_load:
            preserve_radio_layout = QtWidgets.QHBoxLayout()
            preserve_on_radio = QtWidgets.QRadioButton("ON")
            preserve_on_radio.setAutoExclusive(True)
            preserve_on_radio.setChecked(True)
            preserve_on_radio.toggled.connect(lambda: setattr(self, "is_preserve", True) or self.changed_value(True))
            preserve_off_radio = QtWidgets.QRadioButton("OFF")
            preserve_off_radio.setAutoExclusive(True)
            preserve_on_radio.toggled.connect(lambda: setattr(self, "is_preserve", False) or self.changed_value(True))
            preserve_radio_layout.addWidget(preserve_on_radio)
            preserve_radio_layout.addWidget(preserve_off_radio)
            self.model_layout.addRow("Output Shape Type", self.output_shape_type)
            self.model_layout.addRow("Confidence Threshold", self.conf_threshold)
            self.model_layout.addRow("IoU Threshold", self.iou_threshold)
            self.model_layout.addRow("Preserve Existing Annotations", preserve_radio_layout)

            self.update_weight_container(selected_models)

            self.model_layout.addRow("Result Weight", self.container)
            self.model_layout.addRow("", self.total_label)

            button_widget = QtWidgets.QWidget()
            button_layout = QtWidgets.QHBoxLayout()
            self.save_button.clicked.connect(self.save_settings)
            self.apply_current_button.clicked.connect(self.apply_current)
            self.apply_all_button.clicked.connect(self.apply_all)
            button_layout.addWidget(self.save_button)
            button_layout.addWidget(self.apply_current_button)
            button_layout.addWidget(self.apply_all_button)
            button_widget.setLayout(button_layout)
            self.layout().addWidget(button_widget)
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
        self.apply_current_button.setHidden(is_dirty)
        self.apply_all_button.setHidden(is_dirty)

    def save_settings(self):
        if not self.is_total_weight_valid():
            show_critical_message("Error", "Total weight must be 1.0", trace=False)
            return

        CORE.Object.status_bar.showMessage("Saving Object Detection Model settings...")

        for name, box in self.model_weight_value_spinbox:
            CORE.Object.model_manager.active_models("od", [name])
            CORE.Object.model_manager.model_dict[name].model.set_conf_threshold(self.conf_threshold.value())
            CORE.Object.model_manager.model_dict[name].model.set_iou_threshold(self.iou_threshold.value())
            CORE.Object.model_manager.model_dict[name].model.set_is_preserve(self.is_preserve)
            # TODO set weight of each model
            logger.info(CORE.Object.model_manager.model_dict[name])

        logger.info({
            "output_shape_type": self.output_shape_type.currentData(),
            "conf_threshold": self.conf_threshold.value(),
            "iou_threshold": self.iou_threshold.value(),
            "preserve": self.is_preserve,
            "model_weight": [
                {
                    "name": name,
                    "value": box.value()
                } for name, box in self.model_weight_value_spinbox
            ]
        })

        self.changed_value(False)
        CORE.Object.status_bar.showMessage("Object Detection Model settings saved.")

    @staticmethod
    def apply_current():
        result = CORE.Object.model_manager.label_image("od", CORE.Variable.image, CORE.Variable.current_file_full_path)
        logger.info(result.shapes)
        CORE.Object.canvas.new_shapes_from_auto_labeling(result)
        CORE.Object.status_bar.showMessage(f"Generate {len(result.shapes)} shape{'s' if len(result.shapes) > 1 else ''} in current image!")

    def apply_all(self):
        # TODO
        pass
