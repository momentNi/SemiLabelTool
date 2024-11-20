from typing import List

from PyQt5 import QtWidgets, QtCore


class ModelSelectionDialog(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Select applying models")
        self.whole_left_list: List = []
        self.whole_right_list: List = []
        self.origin_right_list: List = []
        self.current_right_list: List = []
        self.current_left_list: List = []

        self.left_selected_count = 0
        self.left_total_count = 0
        self.right_total_count = 0

        layout = QtWidgets.QVBoxLayout()
        main_layout = QtWidgets.QHBoxLayout()

        left_layout = QtWidgets.QVBoxLayout()
        self.left_search_input = QtWidgets.QLineEdit()
        self.left_list_widget = QtWidgets.QListWidget()
        self.left_list_widget.setSelectionMode(QtWidgets.QAbstractItemView.MultiSelection)
        self.left_upload_custom_model_button = QtWidgets.QPushButton("Upload Custom Model")
        self.left_upload_custom_model_button.clicked.connect(self.upload_custom_model)
        self.left_selected_label = QtWidgets.QLabel(f"{self.left_selected_count} Selected")
        self.left_total_label = QtWidgets.QLabel(f"{self.left_total_count} Total")

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
        center_layout.addWidget(self.add_button)
        self.remove_button = QtWidgets.QPushButton("<< Remove")
        center_layout.addWidget(self.remove_button)
        main_layout.addLayout(center_layout)

        right_layout = QtWidgets.QVBoxLayout()
        self.right_search_input = QtWidgets.QLineEdit()
        self.right_list_widget = QtWidgets.QListWidget()
        self.right_list_widget.setSelectionMode(QtWidgets.QAbstractItemView.MultiSelection)
        self.right_clear_button = QtWidgets.QPushButton("Clear selections")
        self.right_clear_button.clicked.connect(self.clear_selections)
        self.right_total_label = QtWidgets.QLabel(f"{self.left_total_count} Total")

        search_layout = QtWidgets.QFormLayout()
        search_layout.addRow("Search Models name", self.right_search_input)
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addWidget(self.right_total_label, 1, QtCore.Qt.AlignLeft)
        button_layout.addWidget(self.right_clear_button, 1, QtCore.Qt.AlignRight)
        right_layout.addLayout(search_layout)
        right_layout.addWidget(self.right_list_widget)
        right_layout.addLayout(button_layout)
        main_layout.addLayout(right_layout)

        bottom_layout = QtWidgets.QHBoxLayout()
        confirm_button = QtWidgets.QPushButton("Confirm")
        confirm_button.clicked.connect(self.confirm_models)

        bottom_layout.addWidget(confirm_button, 0, QtCore.Qt.AlignRight)

        layout.addLayout(main_layout)
        layout.addLayout(bottom_layout)
        self.setLayout(layout)

    def load_default_models(self):
        pass

    def upload_custom_model(self):
        pass

    def clear_selections(self):
        pass

    def confirm_models(self):
        pass
