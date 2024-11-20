from PyQt5 import QtWidgets, QtCore

from core.views.dialogs.model_selection_dialog import ModelSelectionDialog


class SegmentationTab(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.output_shape_type = QtWidgets.QComboBox()
        self.model_weight_box = QtWidgets.QFormLayout()
        self.total_weight = 0.0
        self.is_modified = False

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
        self.model_layout.addRow("Output Shape Type", self.output_shape_type)

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

        save_button = QtWidgets.QPushButton("Save")
        self.layout().addWidget(save_button)

        op_widget = QtWidgets.QWidget()
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

        op_widget.setLayout(op_layout)
        self.layout().addWidget(op_widget)
