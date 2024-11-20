from PyQt5 import QtWidgets, QtCore

from core.views.dialogs.model_selection_dialog import ModelSelectionDialog


class ObjectDetectionTab(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.output_shape_type = QtWidgets.QComboBox()
        self.conf_threshold = QtWidgets.QDoubleSpinBox()
        self.iou_threshold = QtWidgets.QDoubleSpinBox()
        self.model_weight_box = QtWidgets.QFormLayout()
        self.total_weight = 0.0
        self.is_preserve = True

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
        dialog = ModelSelectionDialog()
        dialog.exec_()

        # 选择完成后，更新weight box
        self.update_model_weight_box()

    def update_model_weight_box(self):
        preserve_radio_layout = QtWidgets.QHBoxLayout()
        preserve_on_radio = QtWidgets.QRadioButton("ON")
        preserve_on_radio.setAutoExclusive(True)
        preserve_on_radio.setChecked(True)
        preserve_on_radio.toggled.connect(lambda: setattr(self, "is_preserve", True))
        preserve_off_radio = QtWidgets.QRadioButton("OFF")
        preserve_off_radio.setAutoExclusive(True)
        preserve_on_radio.toggled.connect(lambda: setattr(self, "is_preserve", False))
        preserve_radio_layout.addWidget(preserve_on_radio)
        preserve_radio_layout.addWidget(preserve_off_radio)
        self.model_layout.addRow("Output Shape Type", self.output_shape_type)
        self.model_layout.addRow("Confidence Threshold", self.conf_threshold)
        self.model_layout.addRow("IoU Threshold", self.iou_threshold)
        self.model_layout.addRow("Preserve Existing Annotations", preserve_radio_layout)

        container = QtWidgets.QScrollArea()
        container.setMaximumHeight(400)
        container.setWidgetResizable(True)
        container.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        container.setStyleSheet("border:none")
        weight_box_widget = QtWidgets.QWidget()
        weight_box_widget.adjustSize()
        container.setWidget(weight_box_widget)

        weight_box_layout = QtWidgets.QFormLayout()

        # TODO update model weight box based on selected model
        for i in range(3):
            weight_box_layout.addRow(f"Model {i + 1}", QtWidgets.QDoubleSpinBox())
        # TODO update total weight based on signal of all QSpinBox
        weight_box_widget.setLayout(weight_box_layout)
        self.model_layout.addRow("Result Weight", container)

        total_label = QtWidgets.QLabel(f"Total: {self.total_weight}")
        total_label.setAlignment(QtCore.Qt.AlignRight)
        self.model_layout.addRow("", total_label)

        button_widget = QtWidgets.QWidget()
        button_layout = QtWidgets.QHBoxLayout()
        save_button = QtWidgets.QPushButton("Save")
        apply_current_button = QtWidgets.QPushButton("Apply Current")
        apply_all_button = QtWidgets.QPushButton("Apply All")
        button_layout.addWidget(save_button)
        button_layout.addWidget(apply_current_button)
        button_layout.addWidget(apply_all_button)
        button_widget.setLayout(button_layout)
        self.layout().addWidget(button_widget)
