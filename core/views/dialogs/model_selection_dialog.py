import copy
from typing import List

from PyQt5 import QtWidgets, QtCore


class ModelSelectionDialog(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Select applying models")
        self.whole_left_list: List = []
        self.whole_right_list: List = []
        self.current_right_list: List = []
        self.current_left_list: List = []

        self.left_selected_count = 0
        self.right_selected_count = 0

        layout = QtWidgets.QVBoxLayout()
        main_layout = QtWidgets.QHBoxLayout()

        left_layout = QtWidgets.QVBoxLayout()
        self.left_search_input = QtWidgets.QLineEdit()
        self.left_search_input.setClearButtonEnabled(True)
        self.left_search_input.setPlaceholderText("Search Model names..")
        self.left_search_input.textChanged.connect(self.update_left_list)
        self.left_list_widget = QtWidgets.QListWidget()
        self.left_list_widget.setSelectionMode(QtWidgets.QAbstractItemView.MultiSelection)
        self.left_list_widget.itemSelectionChanged.connect(self.update_label)
        self.left_upload_custom_model_button = QtWidgets.QPushButton("Upload Custom Model")
        self.left_upload_custom_model_button.clicked.connect(self.upload_custom_model)
        self.left_selected_label = QtWidgets.QLabel(f"{self.left_selected_count} Selected")
        self.left_total_label = QtWidgets.QLabel("0 Total")

        search_layout = QtWidgets.QFormLayout()
        search_layout.addRow("Search Models name", self.left_search_input)
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addWidget(self.left_upload_custom_model_button, 1, QtCore.Qt.AlignLeft)
        button_layout.addWidget(self.left_selected_label, 1, QtCore.Qt.AlignCenter)
        button_layout.addWidget(self.left_total_label, 1, QtCore.Qt.AlignRight)
        left_layout.addLayout(search_layout)
        left_layout.addWidget(self.left_list_widget)
        left_layout.addLayout(button_layout)
        main_layout.addLayout(left_layout)

        center_layout = QtWidgets.QVBoxLayout()
        self.add_button = QtWidgets.QPushButton("Add >>")
        self.add_button.clicked.connect(self.add_selected_model)
        self.remove_button = QtWidgets.QPushButton("<< Remove")
        self.remove_button.clicked.connect(self.remove_selected_model)
        self.remove_button.setEnabled(False)
        center_layout.addWidget(self.add_button)
        center_layout.addWidget(self.remove_button)
        main_layout.addLayout(center_layout)

        right_layout = QtWidgets.QVBoxLayout()
        self.right_search_input = QtWidgets.QLineEdit()
        self.right_search_input.setClearButtonEnabled(True)
        self.right_search_input.setPlaceholderText("Search Model names..")
        self.right_search_input.textChanged.connect(self.update_right_list)
        self.right_list_widget = QtWidgets.QListWidget()
        self.right_list_widget.setSelectionMode(QtWidgets.QAbstractItemView.MultiSelection)
        self.right_list_widget.itemSelectionChanged.connect(self.update_label)
        self.right_clear_button = QtWidgets.QPushButton("Clear selections")
        self.right_clear_button.clicked.connect(self.clear_selections)
        self.right_selected_label = QtWidgets.QLabel("0 Selected")
        self.right_total_label = QtWidgets.QLabel("0 Total")

        search_layout = QtWidgets.QFormLayout()
        search_layout.addRow("Search Models name", self.right_search_input)
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addWidget(self.right_selected_label, 1, QtCore.Qt.AlignLeft)
        button_layout.addWidget(self.right_total_label, 1, QtCore.Qt.AlignCenter)
        button_layout.addWidget(self.right_clear_button, 1, QtCore.Qt.AlignRight)
        right_layout.addLayout(search_layout)
        right_layout.addWidget(self.right_list_widget)
        right_layout.addLayout(button_layout)
        main_layout.addLayout(right_layout)

        bottom_layout = QtWidgets.QHBoxLayout()
        self.confirm_button = QtWidgets.QPushButton("Confirm")
        self.confirm_button.clicked.connect(lambda: self.accept())

        bottom_layout.addWidget(self.confirm_button, 0, QtCore.Qt.AlignRight)

        layout.addLayout(main_layout)
        layout.addLayout(bottom_layout)
        self.setLayout(layout)

    def update_label(self):
        self.left_selected_count = len(self.left_list_widget.selectedItems())
        self.add_button.setEnabled(self.left_selected_count != 0)
        self.left_selected_label.setText(f"{self.left_selected_count} Selected")
        self.left_total_label.setText(f"{self.left_list_widget.count()} Total")

        self.right_selected_count = len(self.right_list_widget.selectedItems())
        self.right_selected_label.setText(f"{self.right_selected_count} Selected")
        self.right_total_label.setText(f"{self.right_list_widget.count()} Total")

        self.remove_button.setEnabled(self.right_selected_count != 0)
        self.confirm_button.setEnabled(self.right_list_widget.count() != 0)

    def update_left_list(self):
        if self.left_search_input.text():
            self.current_left_list = [name for name in self.whole_left_list if self.left_search_input.text() in name]
        else:
            self.current_left_list = copy.deepcopy(self.whole_left_list)
        self.left_list_widget.clear()
        self.left_list_widget.addItems(self.current_left_list)
        self.update_label()

    def update_right_list(self):
        if self.right_search_input.text():
            self.current_right_list = [name for name in self.whole_right_list if self.right_search_input.text() in name]
        else:
            self.current_right_list = copy.deepcopy(self.whole_right_list)
        self.right_list_widget.clear()
        self.right_list_widget.addItems(self.current_right_list)
        self.update_label()

    def load_default_models(self, models):
        for name in models:
            self.whole_left_list.append(name)
        self.update_left_list()
        self.update_label()

    def upload_custom_model(self):
        self.left_search_input.clear()
        self.whole_left_list.append("new model")
        self.update_left_list()
        self.update_label()

    def clear_selections(self):
        for item in self.whole_right_list:
            self.whole_left_list.append(item)
        self.update_left_list()
        self.whole_right_list = []
        self.right_list_widget.clear()
        self.update_label()

    def add_selected_model(self):
        selected_items = self.left_list_widget.selectedItems()
        for item in selected_items:
            self.whole_left_list.remove(item.text())
            self.whole_right_list.append(item.text())
        self.update_left_list()
        self.update_right_list()
        self.update_label()

    def remove_selected_model(self):
        selected_items = self.right_list_widget.selectedItems()
        for item in selected_items:
            self.whole_right_list.remove(item.text())
            self.whole_left_list.append(item.text())
        self.update_left_list()
        self.update_right_list()
        self.update_label()
