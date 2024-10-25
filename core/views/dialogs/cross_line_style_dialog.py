from PyQt5 import QtWidgets, QtCore

from core.configs.core import CORE
from core.dto.cross_line import CrossLine


class CrossLineStyleDialog(QtWidgets.QDialog):
    def __init__(self, cross_line: CrossLine):
        super().__init__(CORE.Object.main_window)

        self._show = CORE.Object.canvas.need_show_cross_line
        self._width = cross_line.width
        self._color = cross_line.color
        self._opacity = cross_line.opacity

        self.setWindowTitle("CrossLine Settings")
        self.setModal(True)

        self.show_label = QtWidgets.QLabel("Show CrossLine:")
        self.show_checkbox = QtWidgets.QCheckBox()
        self.show_checkbox.setChecked(self._show)

        self.width_label = QtWidgets.QLabel("Line width:")
        self.width_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.width_slider.setMinimum(10)
        self.width_slider.setMaximum(100)
        self.width_slider.setValue(int(self._width * 10))
        self.width_slider.setTickInterval(1)
        self.width_spinbox = QtWidgets.QDoubleSpinBox()
        self.width_spinbox.setRange(1.0, 10.0)
        self.width_spinbox.setSingleStep(0.1)
        self.width_spinbox.setValue(self._width)

        self.opacity_label = QtWidgets.QLabel("Line Opacity:")
        self.opacity_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.opacity_slider.setMinimum(0)
        self.opacity_slider.setMaximum(100)
        self.opacity_slider.setValue(int(self._opacity * 100))
        self.opacity_slider.setTickInterval(1)
        self.opacity_spinbox = QtWidgets.QDoubleSpinBox()
        self.opacity_spinbox.setRange(0.0, 1.0)
        self.opacity_spinbox.setSingleStep(0.01)
        self.opacity_spinbox.setValue(self._opacity)

        self.color_label = QtWidgets.QLabel("Line Color:")
        self.color_lineedit = QtWidgets.QLineEdit()
        self.color_lineedit.setText(self._color)
        self.color_button = QtWidgets.QPushButton("Choose Color")
        self.color_button.clicked.connect(self.choose_color)

        layout = QtWidgets.QVBoxLayout()
        form_layout = QtWidgets.QFormLayout()
        form_layout.addRow(self.show_label, self.show_checkbox)
        form_layout.addRow(self.width_label, self.width_slider)
        form_layout.addRow("", self.width_spinbox)
        form_layout.addRow(self.opacity_label, self.opacity_slider)
        form_layout.addRow("", self.opacity_spinbox)
        form_layout.addRow(self.color_label, self.color_lineedit)
        form_layout.addRow("", self.color_button)
        layout.addLayout(form_layout)

        button_layout = QtWidgets.QHBoxLayout()

        self.reset_button = QtWidgets.QPushButton("Reset")
        self.reset_button.clicked.connect(self.reset_settings)

        self.button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        button_layout.addWidget(self.reset_button)
        button_layout.addWidget(self.button_box)
        layout.addLayout(button_layout)
        self.setLayout(layout)

        self.width_slider.valueChanged.connect(self.update_width_spinbox)
        self.width_spinbox.valueChanged.connect(self.update_width_slider)
        self.opacity_slider.valueChanged.connect(self.update_opacity_spinbox)
        self.opacity_spinbox.valueChanged.connect(self.update_opacity_slider)

    def update_width_slider(self, value):
        self.width_slider.setValue(int(value * 10))

    def update_width_spinbox(self, value):
        self.width_spinbox.setValue(value / 10.0)

    def update_opacity_slider(self, value):
        self.opacity_slider.setValue(int(value * 100))

    def update_opacity_spinbox(self, value):
        self.opacity_spinbox.setValue(value / 100.0)

    def choose_color(self):
        color = QtWidgets.QColorDialog.getColor()
        if color.isValid():
            self.color_lineedit.setText(color.name())

    def reset_settings(self):
        self.show_checkbox.setChecked(self._show)
        self.width_slider.setValue(int(self._width * 100))
        self.width_spinbox.setValue(self._width)
        self.color_lineedit.setText(self._color)
        self.opacity_slider.setValue(int(self._opacity * 100))
        self.opacity_spinbox.setValue(self._opacity)

    def get_settings(self):
        return {
            "need_show": self.show_checkbox.isChecked(),
            "width": self.width_spinbox.value(),
            "color": self.color_lineedit.text(),
            "opacity": self.opacity_spinbox.value(),
        }
