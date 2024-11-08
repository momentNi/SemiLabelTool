import re

from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import QListWidgetItem

from core.configs.core import CORE
from utils.logger import logger


class LabelDialog(QtWidgets.QDialog):
    def __init__(self, labels=None, flags=None):
        super(LabelDialog, self).__init__(CORE.Object.main_window)
        self.line_edit = LabelQLineEdit()
        self.line_edit.setPlaceholderText("Enter object label")
        self.line_edit.setValidator(QtGui.QRegularExpressionValidator(QtCore.QRegularExpression(r"^[^ \t].+"), None))
        self.line_edit.editingFinished.connect(self.postprocess)
        if flags:
            self.line_edit.textChanged.connect(self.update_flags)

        self.edit_group_id = QtWidgets.QLineEdit()
        self.edit_group_id.setPlaceholderText("Group ID")
        self.edit_group_id.setValidator(QtGui.QRegularExpressionValidator(QtCore.QRegularExpression(r"\d*"), None))
        self.edit_group_id.setAlignment(QtCore.Qt.AlignCenter)

        self.edit_difficult = QtWidgets.QCheckBox("Difficult")
        self.edit_difficult.setChecked(False)

        self.linking_input = QtWidgets.QLineEdit()
        self.linking_input.setPlaceholderText("Enter linking, e.g., [0,1]")
        linking_font = self.linking_input.font()
        linking_font.setPointSize(8)
        self.linking_input.setFont(linking_font)
        self.linking_list = QtWidgets.QListWidget()
        self.linking_list.setHidden(True)
        self.linking_list.setFixedHeight(self.linking_list.fontMetrics().height() * 4 + 2 * self.linking_list.frameWidth())

        self.add_linking_button = QtWidgets.QPushButton("Add")
        self.add_linking_button.clicked.connect(self.add_linking_pair)

        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout_edit = QtWidgets.QHBoxLayout()
        layout_edit.addWidget(self.line_edit, 4)
        layout_edit.addWidget(self.edit_group_id, 2)
        layout.addLayout(layout_edit)

        # Add linking layout
        layout_linking = QtWidgets.QHBoxLayout()
        layout_linking.addWidget(self.linking_input, 4)
        layout_linking.addWidget(self.add_linking_button, 2)
        layout.addLayout(layout_linking)
        layout.addWidget(self.linking_list)

        # buttons
        button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel,
            QtCore.Qt.Horizontal,
            self,
        )
        button_box.accepted.connect(self.validate)
        button_box.rejected.connect(self.reject)

        # text edit
        self.edit_description = QtWidgets.QTextEdit()
        self.edit_description.setPlaceholderText("Label description")
        self.edit_description.setFixedHeight(50)
        layout.addWidget(self.edit_description)

        # difficult & confirm button
        layout_button = QtWidgets.QHBoxLayout()
        layout_button.addWidget(self.edit_difficult)
        layout_button.addWidget(button_box)
        layout.addLayout(layout_button)

        # label_list
        self.label_list = QtWidgets.QListWidget()
        self.label_list.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        if labels:
            self.label_list.addItems(labels)
        self.label_list.sortItems()
        self.label_list.currentItemChanged.connect(self.label_selected)
        self.label_list.itemDoubleClicked.connect(self.label_double_clicked)
        self.line_edit.set_list_widget(self.label_list)
        layout.addWidget(self.label_list)

        if flags is None:
            flags = {}
        self._flags = flags
        self.flags_layout = QtWidgets.QVBoxLayout()
        self.reset_flags()
        layout.addItem(self.flags_layout)
        self.line_edit.textChanged.connect(self.update_flags)
        self.setLayout(layout)

        completer = QtWidgets.QCompleter()
        completer.setCompletionMode(QtWidgets.QCompleter.PopupCompletion)
        completer.setFilterMode(QtCore.Qt.MatchContains)
        completer.setModel(self.label_list.model())
        self.line_edit.setCompleter(completer)

        self._last_label = ""

    def add_linking_pair(self):
        linking_text = self.linking_input.text()
        try:
            linking_pairs = eval(linking_text)
            if isinstance(linking_pairs, list) and len(linking_pairs) == 2 and all(isinstance(item, int) for item in linking_pairs):
                if linking_pairs in self.kie_linking:
                    QtWidgets.QMessageBox.warning(
                        self,
                        "Duplicate Entry",
                        "This linking pair already exists.",
                    )
                self.linking_list.addItem(str(linking_pairs))
                self.linking_input.clear()
                self.linking_list.setHidden(False)
            else:
                raise ValueError
        except Exception as e:
            QtWidgets.QMessageBox.warning(
                self,
                "Invalid Input",
                "Please enter a valid list of linking pairs like [1,2].",
            )
            logger.warning(e)

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Delete:
            selected_items = self.linking_list.selectedItems()
            if selected_items:
                for item in selected_items:
                    self.linking_list.takeItem(self.linking_list.row(item))
                if len(self.kie_linking) == 0:
                    self.linking_list.setHidden(True)
        else:
            super(LabelDialog, self).keyPressEvent(event)

    def remove_linking_item(self, item_widget):
        list_item = QListWidgetItem(self.linking_list.itemWidget(item_widget))
        self.linking_list.takeItem(self.linking_list.row(list_item))
        item_widget.deleteLater()

    def reset_linking(self, kie_linking=None):
        if kie_linking is None:
            kie_linking = []
        self.linking_list.clear()
        for linking_pair in kie_linking:
            self.linking_list.addItem(str(linking_pair))
        self.linking_list.setHidden(False if kie_linking else True)

    def get_last_label(self):
        return self._last_label

    def add_label_history(self, label):
        self._last_label = label
        if self.label_list.findItems(label, QtCore.Qt.MatchExactly):
            return
        self.label_list.addItem(label)
        self.label_list.sortItems()

    def label_selected(self, item):
        self.line_edit.setText(item.text())

    def validate(self):
        text = self.line_edit.text()
        if hasattr(text, "strip"):
            text = text.strip()
        if text:
            self.accept()

    def label_double_clicked(self, _):
        self.validate()

    def postprocess(self):
        text = self.line_edit.text()
        if hasattr(text, "strip"):
            text = text.strip()
        self.line_edit.setText(text)

    def upload_flags(self, flags):
        self._flags = flags

    def update_flags(self, label_new):
        flags_old = self.get_flags()

        flags_new = {}
        for pattern, keys in self._flags.items():
            if re.match(pattern, label_new):
                for key in keys:
                    flags_new[key] = flags_old.get(key, False)
        self.set_flags(flags_new)

    def delete_flags(self):
        for i in reversed(range(self.flags_layout.count())):
            item = self.flags_layout.itemAt(i).widget()
            self.flags_layout.removeWidget(item)

    def reset_flags(self, label=""):
        flags = {}
        for pattern, keys in self._flags.items():
            if re.match(pattern, label):
                for key in keys:
                    flags[key] = False
        self.set_flags(flags)

    def set_flags(self, flags):
        self.delete_flags()
        for key in flags:
            item = QtWidgets.QCheckBox(key, self)
            item.setChecked(flags[key])
            self.flags_layout.addWidget(item)
            item.show()

    def get_flags(self):
        flags = {}
        for i in range(self.flags_layout.count()):
            item = QtWidgets.QCheckBox(self.flags_layout.itemAt(i).widget())
            flags[item.text()] = item.isChecked()
        return flags

    def get_group_id(self):
        group_id = self.edit_group_id.text()
        if group_id:
            return int(group_id)
        return None

    def get_description(self):
        return self.edit_description.toPlainText()

    def get_difficult_state(self):
        return self.edit_difficult.isChecked()

    @property
    def kie_linking(self):
        kie_linking = []
        for index in range(self.linking_list.count()):
            item = self.linking_list.item(index)
            kie_linking.append(eval(item.text()))
        return kie_linking

    def pop_up(self, text=None, move=True, flags=None, group_id=None, description="", is_difficult=False, kie_linking=None):
        if kie_linking is None:
            kie_linking = []
        self.label_list.setMinimumWidth(self.label_list.sizeHintForColumn(0) + 2)
        # if text is None, the previous label in self.edit is kept
        if text is None:
            text = self.line_edit.text()
        # description is always initialized by empty text c.f., self.edit.text
        self.edit_description.setPlainText(description)
        # Set initial values for kie_linking
        self.reset_linking(kie_linking)
        if flags:
            self.set_flags(flags)
        else:
            self.reset_flags(text)
        if is_difficult:
            self.edit_difficult.setChecked(True)
        else:
            self.edit_difficult.setChecked(False)
        self.line_edit.setText(text)
        self.line_edit.setSelection(0, len(text))
        if group_id is None:
            self.edit_group_id.clear()
        else:
            self.edit_group_id.setText(str(group_id))
        items = self.label_list.findItems(text, QtCore.Qt.MatchFixedString)

        if items:
            if len(items) != 1:
                logger.warning(f"Label list has duplicate '{text}'")
            self.label_list.setCurrentItem(items[0])
            row = self.label_list.row(items[0])
            self.line_edit.completer().setCurrentRow(row)
        self.line_edit.setFocus(QtCore.Qt.PopupFocusReason)

        if move:
            cursor_pos = QtGui.QCursor.pos()
            screen = QtWidgets.QApplication.desktop().screenGeometry(cursor_pos)
            dialog_frame_size = self.frameGeometry()
            # Calculate the ideal top-left corner position for the dialog based on the mouse click
            ideal_pos = cursor_pos
            # Adjust to prevent the dialog from exceeding the right screen boundary
            if (ideal_pos.x() + dialog_frame_size.width()) > screen.right():
                ideal_pos.setX(screen.right() - dialog_frame_size.width())
            # Adjust to prevent the dialog's bottom from going off-screen
            if (ideal_pos.y() + dialog_frame_size.height()) > screen.bottom():
                ideal_pos.setY(screen.bottom() - dialog_frame_size.height())
            self.move(ideal_pos)

        if self.exec_():
            return (
                self.line_edit.text(),
                self.get_flags(),
                self.get_group_id(),
                self.get_description(),
                self.get_difficult_state(),
                self.kie_linking,
            )
        return None, None, None, None, False, []


class LabelQLineEdit(QtWidgets.QLineEdit):
    def __init__(self) -> None:
        super().__init__()
        self.list_widget = None

    def set_list_widget(self, list_widget):
        self.list_widget = list_widget

    def keyPressEvent(self, e):
        if e.key() in [QtCore.Qt.Key_Up, QtCore.Qt.Key_Down]:
            self.list_widget.keyPressEvent(e)
        else:
            super(LabelQLineEdit, self).keyPressEvent(e)
