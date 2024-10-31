from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QDockWidget, QPlainTextEdit, QListWidget, QLineEdit

from core.configs.constants import Constants
from core.services import system
from core.services.actions.edit import edit_label
from core.services.signals import files as files_signal
from core.services.signals.views.area.information import *
from core.services.system import load_flags, set_dirty
from core.views.modules.label_filter_combo_box import LabelFilterComboBox
from core.views.modules.label_list_widget import LabelListWidget
from core.views.modules.unique_label_list_widget import UniqueLabelListWidget
from utils.function import get_rgb_by_label


class InformationArea(QWidget):
    def __init__(self, parent=None):
        super().__init__()
        self.parent = parent
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.generate_attribute_dock()
        self.generate_description_dock()
        self.generate_flag_dock()
        self.generate_label_dock()
        self.generate_shape_dock()
        self.generate_file_dock()

        self.setLayout(self.layout)

    def generate_attribute_dock(self):
        attribute_dock = QtWidgets.QDockWidget("Attributes", self)
        attribute_dock.setObjectName("Attributes")
        attribute_dock.setStyleSheet(
            "QDockWidget::title {"
            "text-align: center;"
            "padding: 0px;"
            "background-color: #f0f0f0;"
            "}"
        )

        attribute_dock_layout = QtWidgets.QGridLayout()
        attribute_dock_layout.setContentsMargins(0, 0, 0, 0)
        attribute_dock_layout.setSpacing(0)
        attribute_content_area = QtWidgets.QScrollArea()
        attribute_content_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        attribute_content_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        attribute_content_area.setWidgetResizable(True)
        attribute_dock_layout_container = QWidget()
        attribute_dock_layout_container.setLayout(attribute_dock_layout)
        attribute_content_area.setWidget(attribute_dock_layout_container)

        CORE.Object.attribute_dock = attribute_dock
        CORE.Object.attribute_content_area = attribute_content_area
        # TODO attribute_dock.setHidden(True)
        self.layout.addWidget(attribute_dock)

    def generate_description_dock(self):
        description_dock = QtWidgets.QDockWidget("Description", self)
        description_dock.setObjectName("Description")
        description_dock.setStyleSheet(
            "QDockWidget::title {"
            "text-align: center;"
            "padding: 0px;"
            "background-color: #f0f0f0;"
            "}"
        )
        item_description = QPlainTextEdit()
        item_description.setPlaceholderText("Customize description about selected Object.")
        item_description.textChanged.connect(system.on_item_description_change)
        description_dock.setWidget(item_description)
        CORE.Object.item_description = item_description
        self.layout.addWidget(description_dock)

    def generate_flag_dock(self):
        flag_dock = QtWidgets.QDockWidget("Flags", self)
        flag_dock.setObjectName("FlagDock")
        if CORE.Variable.settings["image_flags"]:
            load_flags({k: False for k in CORE.Variable.settings["image_flags"]})
        else:
            flag_dock.hide()
        CORE.Object.flag_widget = QtWidgets.QListWidget()
        flag_dock.setWidget(CORE.Object.flag_widget)
        CORE.Object.flag_widget.itemChanged.connect(set_dirty)
        flag_dock.setStyleSheet(
            "QDockWidget::title {"
            "text-align: center;"
            "padding: 0px;"
            "background-color: #f0f0f0;"
            "}"
        )
        CORE.Object.flag_dock = flag_dock
        self.layout.addWidget(flag_dock)

    def generate_label_dock(self):
        label_dock = QDockWidget("Labels", self)
        label_dock.setObjectName("LabelDock")
        label_dock.setStyleSheet("""
            QDockWidget::title {
                text-align: center;
                padding: 0px;
                background-color: #f0f0f0;
            }
        """)
        CORE.Object.label_dock = label_dock

        label_filter_combo_box = LabelFilterComboBox(self)
        CORE.Object.label_filter_combo_box = label_filter_combo_box

        unique_label_list = UniqueLabelListWidget()
        unique_label_list.setObjectName("UniqueLabelListWidget")
        unique_label_list.setToolTip("Select label to start annotating for it. Press 'Esc' to deselect.")
        CORE.Object.unique_label_list_widget = unique_label_list

        if CORE.Variable.settings["pre_defined_labels"]:
            for label in CORE.Variable.settings["pre_defined_labels"]:
                item = unique_label_list.create_item_from_label(label)
                unique_label_list.addItem(item)
                rgb = get_rgb_by_label(label)
                unique_label_list.set_item_label(item, label, rgb, Constants.LABEL_OPACITY)

        label_dock_layout = QVBoxLayout()
        label_dock_layout.setContentsMargins(0, 0, 0, 0)
        label_dock_layout.setSpacing(0)
        label_dock_layout.addWidget(label_filter_combo_box)
        label_dock_layout.addWidget(unique_label_list)
        label_dock_widget = QWidget()
        label_dock_widget.setLayout(label_dock_layout)
        label_dock.setWidget(label_dock_widget)

        self.layout.addWidget(label_dock)

    def generate_shape_dock(self):
        shape_dock = QDockWidget("Objects", self)
        shape_dock.setObjectName("ShapeDock")
        shape_dock.setStyleSheet("""
            QDockWidget::title {
                text-align: center;
                padding: 0px;
                background-color: #f0f0f0;
            }
        """)
        CORE.Object.shape_dock = shape_dock

        label_list_widget = LabelListWidget()
        CORE.Object.label_list_widget = label_list_widget
        label_list_widget.item_selection_changed_signal.connect(label_selection_changed)
        label_list_widget.item_double_clicked_signal.connect(edit_label)
        label_list_widget.item_changed.connect(label_item_changed)
        label_list_widget.item_dropped.connect(label_order_changed)

        shape_dock.setWidget(label_list_widget)

        self.layout.addWidget(shape_dock)

    def generate_file_dock(self):
        file_search = QLineEdit()
        file_search.setObjectName("FileSearch")
        file_search.setPlaceholderText(self.tr("Search Filename"))
        file_search.textChanged.connect(file_search_changed)
        CORE.Object.info_file_search_widget = file_search

        file_list_widget = QListWidget()
        file_list_widget.setObjectName("FileList")
        file_list_widget.itemSelectionChanged.connect(files_signal.file_selection_changed)
        CORE.Object.info_file_list_widget = file_list_widget

        file_list_layout = QVBoxLayout()
        file_list_layout.setContentsMargins(0, 0, 0, 0)
        file_list_layout.setSpacing(0)
        file_list_layout.addWidget(file_search)
        file_list_layout.addWidget(file_list_widget)

        file_dock = QDockWidget("Files", self)
        file_dock.setObjectName("FileDock")
        file_list_widget = QWidget()
        file_list_widget.setLayout(file_list_layout)
        file_dock.setWidget(file_list_widget)
        file_dock.setStyleSheet("""
            QDockWidget::title {
                text-align: center;
                padding: 0px;
                background-color: #f0f0f0;
            }
        """)

        CORE.Object.file_dock = file_dock
        self.layout.addWidget(file_dock)
