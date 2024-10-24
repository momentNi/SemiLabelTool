from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QComboBox, QLabel

from core.configs.core import CORE


class LabelFilterComboBox(QWidget):
    def __init__(self, parent=None, items=None):
        super(LabelFilterComboBox, self).__init__(parent)
        if items is None:
            items = []
        self.items = items
        self.combo_box = QComboBox()
        self.combo_box.addItems(self.items)
        self.combo_box.currentIndexChanged.connect(self.combo_selection_changed)

        layout = QHBoxLayout()
        layout.addWidget(QLabel("Filter Labels:"))
        layout.addWidget(self.combo_box)
        self.setLayout(layout)

    def update_items(self, items):
        self.items = items
        self.combo_box.clear()
        self.combo_box.addItems(self.items)

    def combo_selection_changed(self, index):
        label = self.combo_box.itemText(index)
        for item in CORE.Object.label_list_widget:
            if label in ["", item.shape().label]:
                item.setCheckState(Qt.Checked)
            else:
                item.setCheckState(Qt.Unchecked)
