from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QDockWidget


class InformationArea(QWidget):
    def __init__(self, parent=None):
        super().__init__()
        self.parent = parent
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.generate_flag_dock()
        self.generate_label_dock()
        self.generate_item_dock()
        self.generate_file_dock()

        self.setLayout(self.layout)

    def generate_flag_dock(self):
        flag_dock = QtWidgets.QDockWidget(self.tr("Flags"), self)
        flag_dock.setObjectName("FlagDock")
        flag_widget = QtWidgets.QListWidget()
        # if config["flags"]:
        #     self.image_flags = config["flags"]
        #     self.load_flags({k: False for k in self.image_flags})
        # else:
        #     self.flag_dock.hide()
        flag_dock.setWidget(flag_widget)
        # flag_widget.itemChanged.connect(self.set_dirty)
        flag_dock.setStyleSheet(
            "QDockWidget::title {"
            "text-align: center;"
            "padding: 0px;"
            "background-color: #f0f0f0;"
            "}"
        )
        self.layout.addWidget(flag_dock)

    def generate_label_dock(self):
        # label_filter_combobox = LabelFilterComboBox(self)

        # label_list = UniqueLabelQListWidget()
        # label_list.setToolTip(
        #     self.tr(
        #         "Select label to start annotating for it. "
        #         "Press 'Esc' to deselect."
        #     )
        # )
        # if self._config["labels"]:
        #     for label in self._config["labels"]:
        #         item = self.unique_label_list.create_item_from_label(label)
        #         self.unique_label_list.addItem(item)
        #         rgb = self._get_rgb_by_label(label)
        #         self.unique_label_list.set_item_label(
        #             item, label, rgb, LABEL_OPACITY
        #         )

        label_dock = QtWidgets.QDockWidget(self.tr("Labels"), self)
        label_dock.setObjectName("LabelDock")
        # label_dock.setWidget(self.unique_label_list)
        label_dock.setStyleSheet(
            "QDockWidget::title {"
            "text-align: center;"
            "padding: 0px;"
            "background-color: #f0f0f0;"
            "}"
        )
        self.layout.addWidget(label_dock)

    def generate_item_dock(self):
        # label_list = LabelListWidget()
        # label_list.item_selection_changed.connect(
        #     self.label_selection_changed
        # )
        # self.label_list.item_double_clicked.connect(self.edit_label)
        # self.label_list.item_changed.connect(self.label_item_changed)
        # self.label_list.item_dropped.connect(self.label_order_changed)
        shape_dock = QtWidgets.QDockWidget(self.tr("Objects"), self)
        # shape_dock.setWidget(self.label_list)
        shape_dock.setStyleSheet(
            "QDockWidget::title {"
            "text-align: center;"
            "padding: 0px;"
            "background-color: #f0f0f0;"
            "}"
        )
        shape_dock.setTitleBarWidget(QtWidgets.QWidget())

        self.layout.addWidget(shape_dock)

    def generate_file_dock(self):
        file_search = QtWidgets.QLineEdit()
        file_search.setPlaceholderText(self.tr("Search Filename"))
        # file_search.textChanged.connect(self.file_search_changed)

        file_list_widget = QtWidgets.QListWidget()
        # file_list_widget.itemSelectionChanged.connect(
        #     self.file_selection_changed
        # )

        file_list_layout = QVBoxLayout()
        file_list_layout.setContentsMargins(0, 0, 0, 0)
        file_list_layout.setSpacing(0)
        file_list_layout.addWidget(file_search)
        file_list_layout.addWidget(file_list_widget)

        # TODO QGroupBox?
        file_dock = QtWidgets.QDockWidget(self.tr("Files"), self)
        file_dock.setObjectName("FileDock")
        file_list_widget = QtWidgets.QWidget()
        file_list_widget.setLayout(file_list_layout)
        file_dock.setWidget(file_list_widget)
        file_dock.setStyleSheet(
            "QDockWidget::title {"
            "text-align: center;"
            "padding: 0px;"
            "background-color: #f0f0f0;"
            "}"
        )
        file_dock.setFeatures(QDockWidget.DockWidgetFloatable)

        self.layout.addWidget(file_dock)
