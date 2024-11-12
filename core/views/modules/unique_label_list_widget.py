import html
from typing import Tuple

from PyQt5 import QtGui
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt


class EscapableQListWidget(QtWidgets.QListWidget):
    def keyPressEvent(self, event):
        super(EscapableQListWidget, self).keyPressEvent(event)
        if event.key() == Qt.Key_Escape:
            self.clearSelection()


class UniqueLabelListWidget(EscapableQListWidget):
    def find_items_by_label(self, label):
        items = []
        for row in range(self.count()):
            item = self.item(row)
            if item.data(Qt.UserRole) == label:
                items.append(item)
        return items

    @staticmethod
    def create_item_from_label(label: str) -> QtWidgets.QListWidgetItem:
        item = QtWidgets.QListWidgetItem()
        item.setData(Qt.UserRole, label)
        return item

    def set_item_label(self, item: QtWidgets.QListWidgetItem, label: str, color: Tuple[int, int, int], opacity=255):
        q_label = QtWidgets.QLabel()
        if color is None:
            q_label.setText(f"{label}")
        else:
            q_label.setText("{}".format(html.escape(label)))
            background_color = QtGui.QColor(*color, opacity)
            style_sheet = (
                f"background-color: rgba("
                f"{background_color.red()}, "
                f"{background_color.green()}, "
                f"{background_color.blue()}, "
                f"{background_color.alpha()}"
                ");"
            )
            q_label.setStyleSheet(style_sheet)
        q_label.setAlignment(Qt.AlignBottom)
        item.setSizeHint(q_label.sizeHint())
        self.setItemWidget(item, q_label)

    def update_item_color(self, label: str, color, opacity=255):
        items = self.find_items_by_label(label)
        for item in items:
            q_label = self.itemWidget(item)
            if q_label:
                background_color = QtGui.QColor(*color, opacity)
                style_sheet = (
                    f"background-color: rgba("
                    f"{background_color.red()}, "
                    f"{background_color.green()}, "
                    f"{background_color.blue()}, "
                    f"{background_color.alpha()}"
                    ");"
                )
                q_label.setStyleSheet(style_sheet)
                break

    def remove_items_by_label(self, label: str):
        items = self.find_items_by_label(label)
        for item in items:
            row = self.row(item)
            self.takeItem(row)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        if not self.indexAt(event.pos()).isValid():
            self.clearSelection()
