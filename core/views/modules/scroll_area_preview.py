from PyQt5.QtWidgets import QScrollArea, QWidget, QVBoxLayout, QLabel


class ScrollAreaPreview(QScrollArea):
    def __init__(self, *args, **kwargs):
        super(ScrollAreaPreview, self).__init__(*args, **kwargs)

        self.setWidgetResizable(True)

        content = QWidget(self)
        self.setWidget(content)

        layout = QVBoxLayout(content)

        self.label = QLabel(content)
        self.label.setWordWrap(True)

        layout.addWidget(self.label)

    def set_text(self, text):
        self.label.setText(text)

    def set_pixmap(self, pixmap):
        self.label.setPixmap(pixmap)

    def clear(self):
        self.label.clear()
