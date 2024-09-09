from PyQt5.QtWidgets import QMessageBox

import utils
from core.configs.core import CORE
from core.services.actions.file_actions import load_file, load_image_folder
from utils.logger import logger


def file_selection_changed():
    items = CORE.Object.info_file_list.selectedItems()
    if not items:
        return
    item = items[0]

    if not utils.qt_utils.may_continue():
        return

    try:
        current_index = CORE.Variable.image_list.index(str(item.text()))
    except ValueError:
        logger.error(f"File not found: {str(item.text())}")
        QMessageBox.critical(
            CORE.Object.main_window,
            "Error",
            f"File not found: {str(item.text())}",
            QMessageBox.Ok
        )
        return
    if current_index < len(CORE.Variable.image_list):
        filename = CORE.Variable.image_list[current_index]
        if filename:
            load_file(filename)
            # if self.attributes:
            #     # Clear the history widgets from the QGridLayout
            #     self.grid_layout = QGridLayout()
            #     self.grid_layout_container = QWidget()
            #     self.grid_layout_container.setLayout(self.grid_layout)
            #     self.scroll_area.setWidget(self.grid_layout_container)
            #     self.scroll_area.setWidgetResizable(True)
            #     # Create a container widget for the grid layout
            #     self.grid_layout_container = QWidget()
            #     self.grid_layout_container.setLayout(self.grid_layout)
            #     self.scroll_area.setWidget(self.grid_layout_container)


def file_search_changed():
    load_image_folder(
        dir_path=CORE.Variable.last_open_dir_path,
        pattern=CORE.Object.info_file_search.text(),
        need_load=False
    )
