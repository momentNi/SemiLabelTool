import csv
import json
import os

from PyQt5 import QtWidgets, QtCore

from core.configs.core import CORE
from core.dto.enums import ShapeType
from core.services.system import show_critical_message


class ShapeOverviewDialog(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()
        self.image_file_list = [CORE.Object.info_file_list_widget.item(i).text() for i in range(CORE.Object.info_file_list_widget.count())]
        self.start_index = 1
        self.end_index = len(self.image_file_list)
        self.showing_label_infos = True

        if self.image_file_list:
            self.setWindowTitle("Shape Overview")
            self.setWindowFlags(self.windowFlags() | QtCore.Qt.WindowMinimizeButtonHint | QtCore.Qt.WindowMaximizeButtonHint)
            self.resize(800, 600)

            layout = QtWidgets.QVBoxLayout(self)

            self.table = QtWidgets.QTableWidget(self)
            self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
            self.table.resizeRowsToContents()
            self.table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
            self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
            self.populate_table()
            layout.addWidget(self.table)

            self.export_button = QtWidgets.QPushButton("Export")

            range_layout = QtWidgets.QHBoxLayout()

            from_label = QtWidgets.QLabel("From: ")
            self.from_input = QtWidgets.QSpinBox()
            self.from_input.setMinimum(1)
            self.from_input.setMaximum(len(self.image_file_list))
            self.from_input.setSingleStep(1)
            self.from_input.setValue(self.start_index)
            range_layout.addWidget(from_label)
            range_layout.addWidget(self.from_input)

            to_label = QtWidgets.QLabel("To: ")
            self.to_input = QtWidgets.QSpinBox()
            self.to_input.setMinimum(1)
            self.to_input.setMaximum(len(self.image_file_list))
            self.to_input.setSingleStep(1)
            self.to_input.setValue(len(self.image_file_list))
            range_layout.addWidget(to_label)
            range_layout.addWidget(self.to_input)

            self.range_button = QtWidgets.QPushButton("Calculate")
            range_layout.addWidget(self.range_button)
            self.range_button.clicked.connect(self.update_range)

            range_and_export_layout = QtWidgets.QHBoxLayout()
            range_and_export_layout.addWidget(self.export_button, 1, QtCore.Qt.AlignLeft)
            range_and_export_layout.addLayout(range_layout)

            layout.addLayout(range_and_export_layout)

            self.export_button.clicked.connect(self.export_to_csv)

            self.exec_()

    def get_shape_infos(self, start_index: int = -1, end_index: int = -1):
        shape_infos = []

        progress_dialog = QtWidgets.QProgressDialog(
            "Loading...",
            "Cancel",
            0,
            len(self.image_file_list),
        )
        progress_dialog.setMinimumDuration(0)
        progress_dialog.setWindowModality(QtCore.Qt.WindowModal)
        progress_dialog.setWindowTitle("Progress")
        progress_dialog.setStyleSheet(
            """
            QProgressDialog QProgressBar {
                border: 1px solid grey;
                border-radius: 5px;
                text-align: center;
            }
            QProgressDialog QProgressBar::chunk {
                background-color: orange;
            }
            """
        )

        if start_index == -1:
            start_index = self.start_index
        if end_index == -1:
            end_index = self.end_index
        for i, image_file in enumerate(self.image_file_list):
            if i < start_index - 1 or i > end_index - 1:
                continue
            label_dir, filename = os.path.split(image_file)
            if CORE.Variable.output_dir:
                label_dir = CORE.Variable.output_dir
            label_file = os.path.join(label_dir, os.path.splitext(filename)[0] + ".json")
            if not os.path.exists(label_file):
                continue
            with open(label_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            filename = data["imagePath"]
            shapes = data.get("shapes", [])
            for shape in shapes:
                if "label" not in shape or "shape_type" not in shape:
                    continue
                shape_type = shape["shape_type"]
                if shape_type not in list(ShapeType):
                    print(f"Invalid shape_type {shape_type} of {label_file}!")
                    continue
                label = shape["label"]
                score = shape.get("score", 0.0)
                flags = shape.get("flags", {})
                points = shape.get("points", [])
                group_id = shape.get("group_id", -1)
                difficult = shape.get("difficult", False)
                description = shape.get("description", "")
                kie_linking = shape.get("kie_linking", [])
                current_shape = dict(
                    filename=filename,
                    label=label,
                    score=score,
                    flags=flags,
                    points=points,
                    group_id=group_id,
                    difficult=difficult,
                    shape_type=shape_type,
                    description=description,
                    kie_linking=kie_linking,
                )
                shape_infos.append(current_shape)
            progress_dialog.setValue(i)
            if progress_dialog.wasCanceled():
                break
        progress_dialog.close()
        return shape_infos

    def get_shape_infos_table(self, shape_infos):
        headers = [
            "Filename",
            "Label",
            "Type",
            "Linking",
            "Group ID",
            "Difficult",
            "Description",
            "Flags",
            "Points",
        ]
        table_data = []
        for shape in shape_infos:
            row = [
                shape["filename"],
                shape["label"],
                shape["shape_type"],
                str(shape["kie_linking"]),
                str(shape["group_id"]),
                str(shape["difficult"]),
                shape["description"],
                str(shape["flags"]),
                str(shape["points"]),
            ]
            table_data.append(row)
        return headers, table_data

    def populate_table(self, start_index: int = -1, end_index: int = -1):
        shape_infos = self.get_shape_infos(start_index, end_index)
        headers, table_data = self.get_shape_infos_table(shape_infos)
        self.table.setRowCount(len(table_data))
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)

        for row, data in enumerate(table_data):
            for col, value in enumerate(data):
                item = QtWidgets.QTableWidgetItem(value)
                item.setToolTip(value)
                self.table.setItem(row, col, item)
        self.table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)

    def update_range(self):
        from_value = int(self.from_input.text()) if self.from_input.text() else self.start_index
        to_value = int(self.to_input.text()) if self.to_input.text() else self.end_index
        if (from_value > to_value) or \
                (from_value < 1) or (to_value > len(self.image_file_list)):
            self.from_input.setValue(1)
            self.to_input.setValue(len(self.image_file_list))
            self.populate_table(1, len(self.image_file_list))
        else:
            self.start_index = from_value
            self.end_index = to_value
            self.populate_table()

    def export_to_csv(self):
        directory = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Save Directory", "")
        if not directory:
            return

        try:
            # Export shape_infos
            shape_infos = self.get_shape_infos(1, len(self.image_file_list))
            headers, shape_infos_data = self.get_shape_infos_table(shape_infos)
            shape_infos_path = os.path.join(directory, "shape_overview.csv")
            with open(shape_infos_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                for row in shape_infos_data:
                    writer.writerow(row)

            QtWidgets.QMessageBox.information(
                CORE.Object.main_window,
                "Success",
                f"Exporting successfully!\nResults have been saved to: {shape_infos_path}"
            )
        except Exception as e:
            show_critical_message("Error", f"Error occurred while exporting: {e}.")
