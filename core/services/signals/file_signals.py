from core.configs.core import CORE


def file_selection_changed():
    items = CORE.Object.file_list_widget.selectedItems()
    if not items:
        return
    item = items[0]

    if not self.may_continue():
        return

    current_index = self.image_list.index(str(item.text()))
    if current_index < len(self.image_list):
        filename = self.image_list[current_index]
        if filename:
            self.load_file(filename)
            if self.attributes:
                # Clear the history widgets from the QGridLayout
                self.grid_layout = QGridLayout()
                self.grid_layout_container = QWidget()
                self.grid_layout_container.setLayout(self.grid_layout)
                self.scroll_area.setWidget(self.grid_layout_container)
                self.scroll_area.setWidgetResizable(True)
                # Create a container widget for the grid layout
                self.grid_layout_container = QWidget()
                self.grid_layout_container.setLayout(self.grid_layout)
                self.scroll_area.setWidget(self.grid_layout_container)


def file_search_changed():
    self.import_image_folder(
        self.last_open_dir,
        pattern=self.file_search.text(),
        load=False,
    )


def import_image_folder(self, dirpath, pattern=None, load=True):
    self.actions.open_next_image.setEnabled(True)
    self.actions.open_prev_image.setEnabled(True)

    if not self.may_continue() or not dirpath:
        return

    self.last_open_dir = dirpath
    self.filename = None
    self.file_list_widget.clear()
    for filename in self.scan_all_images(dirpath):
        if pattern and pattern not in filename:
            continue
        label_file = osp.splitext(filename)[0] + ".json"
        if self.output_dir:
            label_file_without_path = osp.basename(label_file)
            label_file = self.output_dir + "/" + label_file_without_path
        item = QtWidgets.QListWidgetItem(filename)
        item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
        if QtCore.QFile.exists(label_file) and LabelFile.is_label_file(
                label_file
        ):
            item.setCheckState(Qt.Checked)
        else:
            item.setCheckState(Qt.Unchecked)
        self.file_list_widget.addItem(item)
    self.open_next_image(load=load)