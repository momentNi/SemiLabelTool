import os

from PyQt5 import QtGui, QtCore
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QFileDialog, QListWidgetItem, QMessageBox

import utils
from core.configs.constants import Constants
from core.configs.core import CORE
from core.dto.label_file import LabelFile, LabelFileError
from core.services import system
from core.services.actions import canvas
from core.views.dialogs.brightness_contrast_dialog import BrightnessContrastDialog
from core.views.dialogs.file_dialog_preview import FileDialogPreview
from utils.function import walkthrough_files_in_dir, has_chinese
from utils.image import img_data_to_pil
from utils.video import extract_frames_from_video


def open_file():
    if not utils.qt_utils.may_continue():
        return
    path = os.path.dirname(CORE.Variable.current_file_full_path) if CORE.Variable.current_file_full_path else "."
    formats = [
        f"*.{fmt.data().decode()}"
        for fmt in QtGui.QImageReader.supportedImageFormats()
    ]
    filters = "Image & Label files (%s)" % " ".join(formats + [f"*{LabelFile.suffix}"])
    file_dialog = FileDialogPreview()
    file_dialog.setFileMode(FileDialogPreview.ExistingFile)
    file_dialog.setNameFilter(filters)
    file_dialog.setWindowTitle(f"{Constants.APP_NAME} - Choose Image or Label file")
    file_dialog.setWindowFilePath(path)
    file_dialog.setViewMode(FileDialogPreview.Detail)
    if file_dialog.exec_():
        filename = file_dialog.selectedFiles()[0]
        if filename:
            CORE.Object.info_file_list.clear()
            load_file(filename)


def save_file():
    print("save file")


def load_file(filename: str = None):
    # CORE.Variable.settings.save()

    # For auto labeling, clear the previous marks
    # and inform the next files to be annotated
    # self.clear_auto_labeling_marks()
    # self.inform_next_files(filename)

    # Changing file_list_widget loads file
    if filename in CORE.Variable.image_list and CORE.Object.info_file_list.currentRow() != CORE.Variable.image_list.index(
            filename):
        CORE.Object.info_file_list.setCurrentRow(CORE.Variable.image_list.index(filename))
        CORE.Object.info_file_list.repaint()
        return False

    system.reset_state()
    CORE.Object.canvas.setEnabled(False)
    if not QtCore.QFile.exists(filename):
        CORE.Object.main_window.error_message(
            "Error opening file",
            f"No such file: <b>{filename}</b>"
        )
        return False

    # assumes same name, but json extension
    CORE.Object.status_bar.showMessage(f"Loading {os.path.basename(filename)}...")
    label_file = os.path.splitext(filename)[0] + ".json"
    image_dir = None
    if CORE.Variable.output_dir:
        image_dir = os.path.dirname(filename)
        label_file = os.path.join(CORE.Variable.output_dir, os.path.basename(label_file))
    if QtCore.QFile.exists(label_file) and LabelFile.is_label_file(label_file):
        try:
            CORE.Variable.label_file = LabelFile(label_file, image_dir)
        except LabelFileError as e:
            CORE.Object.main_window.error_message(
                "Error opening file",
                "<p><b>%s</b></p><p>Make sure <i>%s</i> is a valid label file." % (e, label_file)
            )
            CORE.Object.status_bar.showMessage(f"Error reading {label_file}")
            return False
        CORE.Object.item_description.textChanged.disconnect()
        CORE.Object.item_description.setPlainText(CORE.Object.label_file.other_data.get("image_description", ""))
        CORE.Object.item_description.textChanged.connect(system.on_item_description_change)
    else:
        CORE.Variable.label_file = LabelFile()
        CORE.Variable.label_file.load_image_file(filename)
        if CORE.Variable.label_file.image_data:
            CORE.Variable.label_file.image_path = filename
    handling_image = QtGui.QImage.fromData(CORE.Variable.label_file.image_data)

    if handling_image.isNull():
        formats = [
            f"*.{fmt.data().decode()}"
            for fmt in QtGui.QImageReader.supportedImageFormats()
        ]
        CORE.Object.main_window.error_message(
            "Error opening file",
            f"<p>Make sure <i>{filename}</i> is a valid image file.<br/>Supported image formats: {','.join(formats)}</p>"
        )
        CORE.Object.status_bar.showMessage(f"Error reading {filename}")
        return False
    CORE.Variable.image = handling_image
    CORE.Variable.current_file_full_path = filename
    if CORE.Variable.settings["keep_prev"]:
        prev_shapes = CORE.Object.canvas.shapes
        if CORE.Object.canvas.is_no_shape():
            CORE.Object.canvas.load_shapes(prev_shapes, replace=False)
            system.set_dirty()
    else:
        system.set_clean()
    CORE.Object.canvas.load_pixmap(QtGui.QPixmap.fromImage(handling_image))
    # flags = {k: False for k in self.image_flags or []}
    if CORE.Variable.label_file.shapes:
        canvas.load_labels(CORE.Variable.label_file.shapes)
        # if CORE.Variable.label_file.flags is not None:
        #     flags.update(self.label_file.flags)
    # self.load_flags(flags)

    CORE.Object.canvas.setEnabled(True)

    # set zoom values
    is_initial_load = not CORE.Object.canvas.zoom_values
    if CORE.Variable.current_file_full_path in CORE.Object.canvas.zoom_values:
        CORE.Object.canvas.zoom_mode = CORE.Object.canvas.zoom_values[CORE.Variable.current_file_full_path][0]
        system.set_zoom(CORE.Object.canvas.zoom_values[CORE.Variable.current_file_full_path][1])
    elif is_initial_load or not CORE.Variable.settings["keep_prev_scale"]:
        system.adjust_scale(initial=True)

    # set scroll values
    for orientation in CORE.Object.canvas.scroll_values:
        if CORE.Variable.current_file_full_path in CORE.Object.canvas.scroll_values[orientation]:
            CORE.Object.canvas.set_scroll(orientation, CORE.Object.canvas.scroll_values[orientation][
                CORE.Variable.current_file_full_path])

    # set brightness contrast values
    dialog = BrightnessContrastDialog(img_data_to_pil(CORE.Variable.label_file.image_data))
    brightness, contrast = CORE.Variable.brightness_contrast_map.get(CORE.Variable.current_file_full_path, (None, None))
    # if CORE.Variable.settings["keep_prev_brightness"] and self.recent_files:
    #     brightness, _ = self.brightness_contrast_values.get(
    #         self.recent_files[0], (None, None)
    #     )
    # if self._config["keep_prev_contrast"] and self.recent_files:
    #     _, contrast = self.brightness_contrast_values.get(
    #         self.recent_files[0], (None, None)
    #     )
    if brightness is not None:
        dialog.slider_brightness.setValue(brightness)
    if contrast is not None:
        dialog.slider_contrast.setValue(contrast)
    CORE.Variable.brightness_contrast_map[CORE.Variable.current_file_full_path] = (brightness, contrast)
    if brightness is not None or contrast is not None:
        dialog.on_new_value()
    CORE.Object.canvas.paint_canvas()
    # self.add_recent_file(CORE.Variable.current_file_full_path)
    # self.toggle_actions(True)
    CORE.Object.canvas.setFocus()
    basename = os.path.basename(str(filename))
    if CORE.Variable.image_list and filename in CORE.Variable.image_list:
        num_images = len(CORE.Variable.image_list)
        current_index = CORE.Variable.image_list.index(filename) + 1
        msg = f"Loaded {basename} [{current_index}/{num_images}]"
    else:
        msg = f"Loaded {basename}"
    CORE.Object.status_bar.showMessage(msg)
    return True


def open_labeled_image(end_index, step, need_load=True) -> None:
    """
    Open next or previous image

    Args:
        end_index: end index of image in info_file_list
        step: find step
        need_load: load image in canvas when open it in info_file_list
    """
    if not utils.qt_utils.may_continue():
        return
    current_index = CORE.Variable.image_list.index(CORE.Variable.current_file_full_path)
    for i in range(current_index + step, end_index, step):
        if CORE.Object.info_file_list.item(i).checkState() == Qt.Checked:
            CORE.Variable.current_file_full_path = CORE.Variable.image_list[i]
            if CORE.Variable.current_file_full_path and need_load:
                load_file(CORE.Variable.current_file_full_path)
            break


def open_next_image(**kwargs) -> None:
    """
    Open next image to be labeled
    """
    need_load = kwargs.get('need_load', True)
    if QApplication.keyboardModifiers() == (Qt.ControlModifier | Qt.ShiftModifier):
        open_labeled_image(CORE.Object.info_file_list.count(), 1, need_load)
        return

    if not utils.qt_utils.may_continue():
        return

    if len(CORE.Variable.image_list) <= 0:
        return

    if CORE.Variable.current_file_full_path is None:
        filename = CORE.Variable.image_list[0]
    else:
        current_index = CORE.Variable.image_list.index(CORE.Variable.current_file_full_path)
        if current_index + 1 < len(CORE.Variable.image_list):
            filename = CORE.Variable.image_list[current_index + 1]
        else:
            filename = CORE.Variable.image_list[-1]
    CORE.Variable.current_file_full_path = filename

    if CORE.Variable.current_file_full_path and need_load:
        load_file(CORE.Variable.current_file_full_path)


def open_prev_image():
    """
    Open previous image to be labeled
    """
    if QApplication.keyboardModifiers() == (Qt.ControlModifier | Qt.ShiftModifier):
        open_labeled_image(-1, -1)
        return

    if not utils.qt_utils.may_continue():
        return

    if len(CORE.Variable.image_list) <= 0:
        return

    if CORE.Variable.current_file_full_path is None:
        return

    current_index = CORE.Variable.image_list.index(CORE.Variable.current_file_full_path)
    if current_index - 1 >= 0:
        filename = CORE.Variable.image_list[current_index - 1]
        if filename:
            load_file(filename)


def open_directory():
    if not utils.qt_utils.may_continue():
        return

    if CORE.Variable.last_open_dir_path and os.path.exists(CORE.Variable.last_open_dir_path):
        default_open_dir_path = CORE.Variable.last_open_dir_path
    else:
        default_open_dir_path = os.path.dirname(
            CORE.Variable.current_file_full_path) if CORE.Variable.current_file_full_path else "."

    target_dir_path = str(
        QFileDialog.getExistingDirectory(
            CORE.Object.main_window,
            f"{Constants.APP_NAME} - Open Directory",
            default_open_dir_path,
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks,
        )
    )
    load_image_folder(target_dir_path)


def load_image_folder(dir_path, pattern=None, need_load=True):
    CORE.Action.open_next_image.setEnabled(True)
    CORE.Action.open_prev_image.setEnabled(True)

    if not utils.qt_utils.may_continue() or not dir_path:
        return

    CORE.Variable.last_open_dir_path = dir_path
    CORE.Variable.current_file_full_path = None
    CORE.Object.info_file_list.clear()
    for filename in walkthrough_files_in_dir(dir_path):
        if pattern and pattern not in filename:
            continue
        label_file = os.path.splitext(filename)[0] + ".json"
        if CORE.Variable.output_dir:
            label_file = os.path.join(CORE.Variable.output_dir, os.path.basename(label_file))
        item = QListWidgetItem(filename)
        item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
        if QtCore.QFile.exists(label_file) and LabelFile.is_label_file(label_file):
            item.setCheckState(Qt.Checked)
        else:
            item.setCheckState(Qt.Unchecked)
        CORE.Object.info_file_list.addItem(item)
        CORE.Variable.image_list.append(filename)
    open_next_image(need_load=need_load)


def open_video():
    if not utils.qt_utils.may_continue():
        return
    default_open_video_path = (
        os.path.dirname(CORE.Variable.current_file_full_path) if CORE.Variable.current_file_full_path else "."
    )
    source_video_path, _ = QFileDialog.getOpenFileName(
        CORE.Object.main_window,
        f"{Constants.APP_NAME} - Open Video file",
        default_open_video_path,
        "*.asf *.avi *.m4v *.mkv *.mov *.mp4 *.mpeg *.mpg *.ts *.wmv",
    )

    # Check if the path contains Chinese characters
    if has_chinese(source_video_path):
        QMessageBox.warning(
            CORE.Object.main_window,
            "Warning",
            "File path cannot contains Chinese characters",
            QMessageBox.Ok,
        )
        return

    if os.path.exists(source_video_path):
        target_dir_path = extract_frames_from_video(source_video_path)
        load_image_folder(target_dir_path)
