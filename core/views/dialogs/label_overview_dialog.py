import csv
import json
import os

from PyQt5 import QtWidgets, QtCore

from core.configs.core import CORE
from core.dto.enums import ShapeType


class LabelOverviewDialog(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()
        self.image_file_list = [CORE.Object.info_file_list_widget.item(i).text() for i in range(CORE.Object.info_file_list_widget.count())]
        self.start_index = 1
        self.end_index = len(self.image_file_list)
        self.showing_label_infos = True

        if self.image_file_list:
            self.setWindowTitle("Label Overview")
            self.setWindowFlags(self.windowFlags() | QtCore.Qt.WindowMinimizeButtonHint | QtCore.Qt.WindowMaximizeButtonHint)
            self.resize(800, 600)

            layout = QtWidgets.QVBoxLayout(self)

            self.table = QtWidgets.QTableWidget(self)
            self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
            self.table.resizeRowsToContents()
            self.table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
            self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
            self.total_table = QtWidgets.QTableWidget(self)
            self.total_table.setRowCount(1)
            self.total_table.setVerticalHeaderLabels([" "])
            self.total_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
            self.total_table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
            self.total_table.setMaximumHeight(55)
            self.populate_table()
            layout.addWidget(self.table, 1)
            layout.addWidget(self.total_table)

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
            range_layout.addStretch(1)

            range_and_export_layout = QtWidgets.QHBoxLayout()
            range_and_export_layout.addWidget(self.export_button, 1, QtCore.Qt.AlignLeft)
            range_and_export_layout.addLayout(range_layout)

            layout.addLayout(range_and_export_layout)

            self.export_button.clicked.connect(self.export_to_csv)

            self.exec_()

    def get_label_infos(self, start_index: int = -1, end_index: int = -1):
        initial_nums = [0 for _ in range(len(list(ShapeType)))]
        label_infos = {}

        progress_dialog = QtWidgets.QProgressDialog(
            "Loading...",
            "Cancel",
            0,
            len(self.image_file_list),
        )
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
            shapes = data.get("shapes", [])
            for shape in shapes:
                label = shape.get("label", None)
                shape_type = shape.get("shape_type", None)
                if label is None or shape_type not in list(ShapeType):
                    continue
                if label not in label_infos:
                    label_infos[label] = dict(zip(list(ShapeType), initial_nums))
                label_infos[label][shape_type] += 1
            progress_dialog.setValue(i)
            if progress_dialog.wasCanceled():
                break
        progress_dialog.close()
        return {k: label_infos[k] for k in sorted(label_infos)}

    def get_total_infos(self, start_index: int = -1, end_index: int = -1):
        label_infos = self.get_label_infos(start_index, end_index)
        total_infos = [["Label"] + [item.name for item in list(ShapeType)] + ["Total"]]
        shape_counter = [0 for _ in range(len(list(ShapeType)) + 1)]

        for label, infos in label_infos.items():
            counter = [
                infos[shape_type] for shape_type in list(ShapeType)
            ]
            counter.append(sum(counter))
            row = [label] + counter
            total_infos.append(row)
            shape_counter = [x + y for x, y in zip(counter, shape_counter)]

        total_infos.append(["Total"] + shape_counter)
        self.total_table.setColumnCount(len(shape_counter) + 1)
        self.total_table.setHorizontalHeaderLabels([""] + [item.name for item in list(ShapeType)] + ["Total"])
        total_item = QtWidgets.QTableWidgetItem("Total")
        total_item.setTextAlignment(QtCore.Qt.AlignCenter)
        self.total_table.setItem(0, 0, total_item)
        for i in range(len(shape_counter)):
            item = QtWidgets.QTableWidgetItem(str(shape_counter[i]))
            item.setTextAlignment(QtCore.Qt.AlignCenter)
            self.total_table.setItem(0, i + 1, item)
        return total_infos

    def populate_table(self, start_index: int = -1, end_index: int = -1):
        total_infos = self.get_total_infos(start_index, end_index)
        self.table.setRowCount(len(total_infos) - 2)
        self.table.setColumnCount(len(total_infos[0]))
        self.table.setHorizontalHeaderLabels(total_infos[0])

        data = [list(map(str, info)) for info in total_infos[1:-1]]

        for row, info in enumerate(data):
            for col, value in enumerate(info):
                item = QtWidgets.QTableWidgetItem(value)
                item.setTextAlignment(QtCore.Qt.AlignCenter)
                self.table.setItem(row, col, item)

    def update_range(self):
        from_value = int(self.from_input.text()) if self.from_input.text() else self.start_index
        to_value = int(self.to_input.text()) if self.to_input.text() else self.end_index
        if (from_value > to_value) or (from_value < 1) or (to_value > len(self.image_file_list)):
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
            label_infos = self.get_total_infos(1, len(self.image_file_list))
            label_infos_path = os.path.join(directory, "label_overview.csv")
            with open(label_infos_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                for row in label_infos:
                    writer.writerow(row)

            QtWidgets.QMessageBox.information(
                CORE.Object.main_window,
                "Success",
                f"Exporting successfully!\nResults have been saved to: {label_infos_path}"
            )
        except Exception as e:
            QtWidgets.QMessageBox.critical(
                CORE.Object.main_window,
                "Error",
                f"Error occurred while exporting: {e}.\nPlease check the log file for more details."
            )
