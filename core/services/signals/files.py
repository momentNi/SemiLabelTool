from PyQt5 import QtWidgets

import utils
from core.configs.core import CORE
from core.services.actions import files as files_action
from core.services.system import show_critical_message


def file_selection_changed():
    items = CORE.Object.info_file_list_widget.selectedItems()
    if not items:
        return
    item = items[0]

    if not utils.qt_utils.may_continue():
        return

    try:
        current_index = CORE.Variable.image_list.index(str(item.text()))
    except ValueError:
        show_critical_message("Error", f"File not found: {str(item.text())}")
        return
    if current_index < len(CORE.Variable.image_list):
        filename = CORE.Variable.image_list[current_index]
        if filename:
            files_action.load_file(filename)
            if CORE.Variable.attributes:
                # Clear the history widgets from the QGridLayout
                grid_layout = QtWidgets.QGridLayout()
                grid_layout_container = QtWidgets.QWidget()
                grid_layout_container.setLayout(grid_layout)
                CORE.Object.attribute_content_area.setWidget(grid_layout_container)
                CORE.Object.attribute_content_area.setWidgetResizable(True)
                # Create a container widget for the grid layout
                grid_layout_container = QtWidgets.QWidget()
                grid_layout_container.setLayout(grid_layout)
                CORE.Object.attribute_content_area.setWidget(grid_layout_container)
