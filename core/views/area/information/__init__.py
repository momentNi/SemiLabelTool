from PyQt5 import QtWidgets, QtCore

from core.configs.constants import Constants
from core.configs.core import CORE
from core.services import system
from core.services.actions.edit import edit_label
from core.services.signals import files as files_signal
from core.services.signals.views.area.information import label_selection_changed, label_item_changed, label_order_changed, file_search_changed
from core.views.modules.label_filter_combo_box import LabelFilterComboBox
from core.views.modules.label_list_widget import LabelListWidget
from core.views.modules.unique_label_list_widget import UniqueLabelListWidget
from utils.function import get_rgb_by_label


class InformationArea(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__()
        self.parent = parent

        self.layout = QtWidgets.QVBoxLayout()

        self.tab_widget = QtWidgets.QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.setMovable(True)
        self.tab_widget.setTabPosition(QtWidgets.QTabWidget.East)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        CORE.Object.tab_widget = self.tab_widget

        self.generate_file_tab()
        self.generate_label_tab()
        self.generate_image_tab()

        self.layout.addWidget(self.tab_widget)
        self.setLayout(self.layout)

    def generate_file_tab(self):
        if CORE.Object.file_tab_widget is not None:
            self.tab_widget.addTab(CORE.Object.file_tab_widget, "Files")
        else:
            if CORE.Object.info_file_search_widget is None:
                file_search = QtWidgets.QLineEdit()
                file_search.setClearButtonEnabled(True)
                file_search.setObjectName("FileSearch")
                file_search.setPlaceholderText("Search Filename")
                file_search.textChanged.connect(file_search_changed)
                CORE.Object.info_file_search_widget = file_search
            else:
                file_search = CORE.Object.info_file_search_widget

            if CORE.Object.info_file_list_widget is None:
                file_list_widget = QtWidgets.QListWidget()
                file_list_widget.setObjectName("FileList")
                file_list_widget.itemSelectionChanged.connect(files_signal.file_selection_changed)
                CORE.Object.info_file_list_widget = file_list_widget
            else:
                file_list_widget = CORE.Object.info_file_list_widget

            file_tab_layout = QtWidgets.QVBoxLayout()
            file_tab_layout.addWidget(file_search)
            file_tab_layout.addWidget(file_list_widget)
            file_tab_widget = QtWidgets.QWidget()
            file_tab_widget.setLayout(file_tab_layout)

            CORE.Object.file_tab_widget = file_tab_widget

            self.tab_widget.addTab(file_tab_widget, "Files")

    def generate_label_tab(self):
        if CORE.Object.label_tab_widget is not None:
            self.tab_widget.addTab(CORE.Object.label_tab_widget, "Labels")
        else:
            if CORE.Object.label_filter_combo_box is None:
                label_filter_combo_box = LabelFilterComboBox(self)
                CORE.Object.label_filter_combo_box = label_filter_combo_box
            else:
                label_filter_combo_box = CORE.Object.label_filter_combo_box

            if CORE.Object.unique_label_list_widget is None:
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
            else:
                unique_label_list = CORE.Object.unique_label_list_widget

            if CORE.Object.label_list_widget is None:
                label_list_widget = LabelListWidget()
                label_list_widget.item_selection_changed_signal.connect(label_selection_changed)
                label_list_widget.item_double_clicked_signal.connect(edit_label)
                label_list_widget.item_changed.connect(label_item_changed)
                label_list_widget.item_dropped.connect(label_order_changed)
                CORE.Object.label_list_widget = label_list_widget
            else:
                label_list_widget = CORE.Object.label_list_widget

            label_box = QtWidgets.QGroupBox()
            label_box.setTitle("Labels")
            label_box_layout = QtWidgets.QVBoxLayout()
            label_box_layout.addWidget(label_filter_combo_box)
            label_box_layout.addWidget(unique_label_list)
            label_box.setLayout(label_box_layout)

            shape_box = QtWidgets.QGroupBox()
            shape_box.setTitle("Shapes")
            shape_box_layout = QtWidgets.QVBoxLayout()
            shape_box_layout.addWidget(label_list_widget)
            shape_box.setLayout(shape_box_layout)

            label_tab_layout = QtWidgets.QVBoxLayout()
            label_tab_layout.addWidget(label_box)
            label_tab_layout.addWidget(shape_box)
            label_tab_widget = QtWidgets.QWidget()
            label_tab_widget.setLayout(label_tab_layout)

            CORE.Object.label_tab_widget = label_tab_widget
            self.tab_widget.addTab(label_tab_widget, "Labels")

    def generate_image_tab(self):
        if CORE.Object.image_tab_widget is not None:
            self.tab_widget.addTab(CORE.Object.image_tab_widget, "Image")
        else:
            description_box = QtWidgets.QGroupBox()
            description_box.setTitle("Description")
            description_box_layout = QtWidgets.QVBoxLayout()
            if CORE.Object.item_description is None:
                item_description = QtWidgets.QPlainTextEdit()
                item_description.setPlaceholderText("Customize description about selected Object.")
                item_description.textChanged.connect(system.on_item_description_change)
                CORE.Object.item_description = item_description
            description_box_layout.addWidget(CORE.Object.item_description)
            description_box.setLayout(description_box_layout)

            flag_box = QtWidgets.QGroupBox()
            flag_box.setTitle("Flags")
            flag_box_layout = QtWidgets.QVBoxLayout()
            if CORE.Object.flag_widget is None:
                CORE.Object.flag_widget = QtWidgets.QListWidget()
                if CORE.Variable.settings["image_flags"]:
                    system.load_flags({k: False for k in CORE.Variable.settings["image_flags"]})
                CORE.Object.flag_widget.itemChanged.connect(system.set_dirty)
            flag_box_layout.addWidget(CORE.Object.flag_widget)
            flag_box.setLayout(flag_box_layout)

            attributes_box = QtWidgets.QGroupBox()
            attributes_box.setTitle("Attributes")
            attributes_box_layout = QtWidgets.QVBoxLayout()
            if CORE.Object.attribute_content_area is None:
                attribute_dock_layout = QtWidgets.QGridLayout()
                attribute_dock_layout.setSpacing(0)
                attribute_content_area = QtWidgets.QScrollArea()
                attribute_content_area.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
                attribute_content_area.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
                attribute_content_area.setWidgetResizable(True)
                attribute_dock_layout_container = QtWidgets.QWidget()
                attribute_dock_layout_container.setLayout(attribute_dock_layout)
                attribute_content_area.setWidget(attribute_dock_layout_container)
                CORE.Object.attribute_content_area = attribute_content_area
            attributes_box_layout.addWidget(CORE.Object.attribute_content_area)
            attributes_box.setLayout(attributes_box_layout)

            image_tab_layout = QtWidgets.QVBoxLayout()
            image_tab_layout.addWidget(description_box)
            if flag_box is not None:
                image_tab_layout.addWidget(flag_box)
            image_tab_layout.addWidget(attributes_box)
            image_tab_widget = QtWidgets.QWidget()
            image_tab_widget.setLayout(image_tab_layout)

            CORE.Object.image_tab_widget = image_tab_widget
            self.tab_widget.addTab(image_tab_widget, "Images")

    def close_tab(self, index):
        tab_name = self.tab_widget.tabText(index)
        if tab_name == "Files":
            CORE.Action.file_tab_toggle.setChecked(False)
        elif tab_name == "Labels":
            CORE.Action.label_tab_toggle.setChecked(False)
        elif tab_name == "Images":
            CORE.Action.image_tab_toggle.setChecked(False)

        self.tab_widget.removeTab(index)
