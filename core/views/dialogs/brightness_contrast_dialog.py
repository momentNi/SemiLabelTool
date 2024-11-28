import PIL.Image
import PIL.ImageEnhance
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QDialog, QWidget, QLabel, QHBoxLayout, QPushButton, QVBoxLayout, QSlider

from core.configs.core import CORE
from core.services.system import show_critical_message


class BrightnessContrastDialog(QDialog):
    def __init__(self, img):
        super(BrightnessContrastDialog, self).__init__(CORE.Object.main_window)
        self.setModal(True)
        self.setWindowTitle("Brightness/Contrast")

        if not isinstance(img, PIL.Image.Image):
            show_critical_message("Error opening file", "Image must be PIL.Image", trace=False)
            return

        self.img = img
        self.original_img = img.copy()

        # Brightness slider and label
        self.slider_brightness = self.__create_slider()
        self.brightness_label = QLabel(f"{self.slider_brightness.value() / 50:.2f}")
        self.slider_brightness.valueChanged.connect(self.update_brightness_label)

        brightness_layout = QHBoxLayout()
        brightness_layout.addWidget(QLabel(self.tr("Brightness: ")))
        brightness_layout.addWidget(self.slider_brightness)
        brightness_layout.addWidget(self.brightness_label)

        brightness_widget = QWidget()
        brightness_widget.setLayout(brightness_layout)

        # Contrast slider and label
        self.slider_contrast = self.__create_slider()
        self.contrast_label = QLabel(f"{self.slider_contrast.value() / 50:.2f}")
        self.slider_contrast.valueChanged.connect(self.update_contrast_label)

        contrast_layout = QHBoxLayout()
        contrast_layout.addWidget(QLabel(self.tr("Contrast:    ")))
        contrast_layout.addWidget(self.slider_contrast)
        contrast_layout.addWidget(self.contrast_label)

        contrast_widget = QWidget()
        contrast_widget.setLayout(contrast_layout)

        # Reset button
        self.reset_button = QPushButton(self.tr("Reset"))
        self.reset_button.clicked.connect(self.reset_values)

        # Confirm button
        self.confirm_button = QPushButton(self.tr("Confirm"))
        self.confirm_button.clicked.connect(self.confirm_values)

        # Buttons layout
        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(self.reset_button)
        buttons_layout.addWidget(self.confirm_button)

        # Main layout
        main_layout = QVBoxLayout()
        main_layout.addWidget(brightness_widget)
        main_layout.addWidget(contrast_widget)
        main_layout.addLayout(buttons_layout)
        self.setLayout(main_layout)

    @staticmethod
    def __create_slider():
        slider = QSlider(Qt.Horizontal)
        slider.setRange(0, 150)
        slider.setValue(50)
        return slider

    def update_brightness_label(self, value):
        self.brightness_label.setText(f"{value / 50:.2f}")
        self.on_new_value()

    def update_contrast_label(self, value):
        self.contrast_label.setText(f"{value / 50:.2f}")
        self.on_new_value()

    def on_new_value(self):
        brightness = self.slider_brightness.value() / 50.0
        contrast = self.slider_contrast.value() / 50.0

        img = self.img
        if brightness != 1:
            img = PIL.ImageEnhance.Brightness(img).enhance(brightness)
        if contrast != 1:
            img = PIL.ImageEnhance.Contrast(img).enhance(contrast)

        img = img.convert("RGB")
        q_image = QImage(img.tobytes(), img.width, img.height, QImage.Format_RGB888)
        CORE.Object.canvas.load_pixmap(QPixmap.fromImage(q_image), clear_shapes=False)

    def reset_values(self):
        self.slider_brightness.setValue(50)
        self.slider_contrast.setValue(50)
        self.img = self.original_img.copy()
        self.on_new_value()

    def confirm_values(self):
        self.accept()
