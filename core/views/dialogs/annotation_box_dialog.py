import json
import traceback

from PyQt5 import QtWidgets, QtCore, QtGui

from core.configs.constants import Constants
from core.configs.core import CORE
from core.services import system
from utils.function import get_rgb_by_label
from utils.logger import logger


class AnnotationBoxDialog(QtWidgets.QDialog):
    def __init__(self):
        super(AnnotationBoxDialog, self).__init__()
        self.setWindowTitle("Annotation Boxes Settings")
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.WindowMinimizeButtonHint | QtCore.Qt.WindowMaximizeButtonHint)
        self.resize(800, 600)

        self.label_file_list = system.get_label_file_list()

        self.table_widget = QtWidgets.QTableWidget(self)

        self.init_label_info()
        self.init_ui()
        self.populate_table()

    def init_label_info(self):
        classes = set()

        for label_file in self.label_file_list:
            with open(label_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            shapes = data.get("shapes", [])
            for shape in shapes:
                label = shape["label"]
                classes.add(label)

        for cls in sorted(classes):
            if not CORE.Object.unique_label_list_widget.find_items_by_label(cls):
                unique_label_item = CORE.Object.unique_label_list_widget.create_item_from_label(cls)
                CORE.Object.unique_label_list_widget.addItem(unique_label_item)
                rgb = get_rgb_by_label(cls)
                CORE.Object.unique_label_list_widget.set_item_label(unique_label_item, cls, rgb, Constants.LABEL_OPACITY)

            color = [0, 0, 0]
            opacity = 255
            items = CORE.Object.unique_label_list_widget.find_items_by_label(cls)
            for item in items:
                q_label = CORE.Object.unique_label_list_widget.itemWidget(item)
                if q_label:
                    style_sheet = q_label.styleSheet()
                    start_index = style_sheet.find('rgba(') + 5
                    end_index = style_sheet.find(')', start_index)
                    rgba_color = style_sheet[start_index:end_index].split(',')
                    rgba_color = [int(x.strip()) for x in rgba_color]
                    color = rgba_color[:-1]
                    opacity = rgba_color[-1]
                    break
            CORE.Variable.label_info[cls] = dict(value=None, color=color, opacity=opacity, hidden=cls in CORE.Variable.hidden_class_list, delete=False)

    def init_ui(self):
        self.table_widget.setColumnCount(5)
        self.table_widget.setHorizontalHeaderLabels(["Label", "New Value", "Color", "Hidden", "Delete"])

        for i in range(5):
            self.table_widget.horizontalHeaderItem(i).setFont(QtGui.QFont("Arial", 8, QtGui.QFont.Bold))
            self.table_widget.horizontalHeaderItem(i).setTextAlignment(QtCore.Qt.AlignCenter)

        buttons_layout = QtWidgets.QHBoxLayout()

        cancel_button = QtWidgets.QPushButton("Cancel", self)
        cancel_button.clicked.connect(self.reject)

        confirm_button = QtWidgets.QPushButton("Confirm", self)
        confirm_button.clicked.connect(self.confirm_changes)
        confirm_button.setDefault(True)

        buttons_layout.addStretch(1)
        buttons_layout.addWidget(cancel_button)
        buttons_layout.addStretch(1)
        buttons_layout.addWidget(confirm_button)
        buttons_layout.addStretch(1)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.table_widget)
        layout.addLayout(buttons_layout)

    def populate_table(self):
        for i, (label, info) in enumerate(CORE.Variable.label_info.items()):
            self.table_widget.insertRow(i)

            class_item = QtWidgets.QTableWidgetItem(label)
            class_item.setFlags(class_item.flags() ^ QtCore.Qt.ItemIsEditable)

            delete_checkbox = QtWidgets.QCheckBox()
            delete_checkbox.setChecked(info["delete"])
            delete_checkbox.setIcon(QtGui.QIcon(":/images/images/delete.png"))
            delete_checkbox.stateChanged.connect(lambda state, row=i: self.on_delete_checkbox_changed(row, state))
            delete_checkbox.setCheckable(not info["hidden"])

            hidden_checkbox = QtWidgets.QCheckBox()
            hidden_checkbox.setChecked(info["hidden"])
            hidden_checkbox.setIcon(QtGui.QIcon(":/images/images/hidden.png"))
            hidden_checkbox.stateChanged.connect(lambda state, row=i: self.on_hidden_checkbox_changed(row, state))

            value_item = QtWidgets.QTableWidgetItem(info["value"] if info["value"] else "")
            value_item.setFlags(value_item.flags() & ~QtCore.Qt.ItemIsEditable if info["delete"] else value_item.flags() | QtCore.Qt.ItemIsEditable)
            value_item.setBackground(QtGui.QColor("lightgray") if info["delete"] else QtGui.QColor("white"))

            color = QtGui.QColor(*info['color'])
            color.setAlpha(info['opacity'])
            color_button = LabelColorButton(color, self)
            color_button.setParent(self.table_widget)

            self.table_widget.setItem(i, 0, class_item)
            self.table_widget.setItem(i, 1, value_item)
            self.table_widget.setCellWidget(i, 2, color_button)
            self.table_widget.setCellWidget(i, 3, hidden_checkbox)
            self.table_widget.setCellWidget(i, 4, delete_checkbox)

    def change_color(self, button):
        row = self.table_widget.indexAt(button.pos()).row()
        current_color = CORE.Variable.label_info[self.table_widget.item(row, 0).text()]['color']
        color = QtWidgets.QColorDialog.getColor(QtGui.QColor(*current_color), self)
        if color.isValid():
            CORE.Variable.label_info[self.table_widget.item(row, 0).text()]['color'] = [color.red(), color.green(), color.blue()]
            CORE.Variable.label_info[self.table_widget.item(row, 0).text()]['opacity'] = color.alpha()
            button.set_color(color)

    def on_delete_checkbox_changed(self, row, state):
        value_item = self.table_widget.item(row, 1)
        hidden_checkbox = self.table_widget.cellWidget(row, 3)
        delete_checkbox = self.table_widget.cellWidget(row, 4)

        if state == QtCore.Qt.Checked:
            value_item.setFlags(value_item.flags() & ~QtCore.Qt.ItemIsEditable)
            value_item.setBackground(QtGui.QColor("lightgray"))
            delete_checkbox.setCheckable(True)
            hidden_checkbox.setCheckable(False)
        else:
            value_item.setFlags(value_item.flags() | QtCore.Qt.ItemIsEditable)
            value_item.setBackground(QtGui.QColor("white"))
            delete_checkbox.setCheckable(False)
            hidden_checkbox.setCheckable(True)

        if value_item.text():
            delete_checkbox.setCheckable(False)
        else:
            delete_checkbox.setCheckable(True)

    def on_hidden_checkbox_changed(self, row, state):
        delete_checkbox = self.table_widget.cellWidget(row, 4)

        if state == QtCore.Qt.Checked:
            delete_checkbox.setCheckable(False)
        else:
            delete_checkbox.setCheckable(True)

    def confirm_changes(self):
        CORE.Variable.hidden_class_list.clear()

        total_num = self.table_widget.rowCount()
        if total_num == 0:
            self.reject()
            return

        temp_new_label_info_map = {}

        for i in range(total_num):
            label = self.table_widget.item(i, 0).text()
            new_value = self.table_widget.item(i, 1).text()
            is_hidden = self.table_widget.cellWidget(i, 3).isChecked()
            is_delete = self.table_widget.cellWidget(i, 4).isChecked()

            CORE.Variable.label_info[label]["delete"] = is_delete
            CORE.Variable.label_info[label]["value"] = new_value

            if not is_delete and is_hidden:
                CORE.Variable.hidden_class_list.append(label if new_value == "" else new_value)

            color = CORE.Variable.label_info[label]["color"]
            CORE.Object.unique_label_list_widget.update_item_color(label, color, Constants.LABEL_OPACITY)

            if is_delete:
                CORE.Object.unique_label_list_widget.remove_items_by_label(label)
                continue
            elif new_value:
                CORE.Object.unique_label_list_widget.remove_items_by_label(label)
                temp_new_label_info_map[new_value] = CORE.Variable.label_info[label]
            else:
                temp_new_label_info_map[label] = CORE.Variable.label_info[label]

        if self.modify_label():
            CORE.Variable.label_info = temp_new_label_info_map
            QtWidgets.QMessageBox.information(
                self,
                "Success",
                "Labels modified successfully!",
            )
            self.accept()
        else:
            QtWidgets.QMessageBox.warning(
                self,
                "Warning",
                "An error occurred while updating the labels."
            )

    def modify_label(self):
        try:
            for label_file in self.label_file_list:
                with open(label_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                src_shapes, dst_shapes = data["shapes"], []
                for shape in src_shapes:
                    label = shape["label"]
                    if CORE.Variable.label_info[label]["delete"]:
                        continue
                    if CORE.Variable.label_info[label]["value"]:
                        shape["label"] = CORE.Variable.label_info[label]["value"]
                    shape["visible"] = CORE.Variable.label_info[label]["hidden"]
                    dst_shapes.append(shape)
                data["shapes"] = dst_shapes
                with open(label_file, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception:
            logger.error(traceback.print_exc())
            return False


class LabelColorButton(QtWidgets.QWidget):
    def __init__(self, color, parent: AnnotationBoxDialog = None):
        super().__init__(parent)
        self.color = color
        self.parent: AnnotationBoxDialog = parent
        self.color_label = QtWidgets.QLabel()
        self.layout = QtWidgets.QHBoxLayout(self)

        self.init_ui()

    def init_ui(self):
        self.color_label.setFixedSize(15, 15)
        self.color_label.setStyleSheet(f'background-color: {self.color.name()}; border: 1px solid transparent; border-radius: 10px;')

        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.addWidget(self.color_label)

    def set_color(self, color):
        self.color = color
        self.color_label.setStyleSheet(f'background-color: {self.color.name()}; border: 1px solid transparent; border-radius: 10px;')

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            AnnotationBoxDialog.change_color(self.parent, button=self)
