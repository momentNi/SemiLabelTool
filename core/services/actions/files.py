import functools
import os

from PyQt5 import QtGui, QtCore, QtWidgets
from PyQt5.QtCore import Qt

import utils
from core.configs.constants import Constants
from core.configs.core import CORE
from core.dto.enums import ShapeType, AutoLabelEditMode
from core.dto.exceptions import LabelFileError
from core.dto.label_file import LabelFile
from core.services import system
from core.services.actions.canvas import paint_canvas, set_scroll_value
from core.services.system import set_clean, reset_state, load_flags, set_dirty, set_zoom, adjust_scale, on_item_description_change, toggle_zoom_related_action, toggle_load_related_action
from core.views.dialogs.brightness_contrast_dialog import BrightnessContrastDialog
from core.views.dialogs.file_dialog_preview import FileDialogPreview
from core.views.dialogs.save_file_dialog import SaveFileDialog
from utils.function import walkthrough_files_in_dir, has_chinese
from utils.image import img_data_to_pil
from utils.logger import logger
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
            CORE.Object.info_file_list_widget.clear()
            load_file(filename)


def save_label_file(filename: str):
    if filename and save_labels(filename):
        add_recent_file(filename)
        set_clean()


def save_labels(filename):
    label_file = LabelFile()

    def format_shape(s):
        data = s.other_data.copy()
        info = {
            "label": s.label,
            "score": s.score,
            "points": [(p.x(), p.y()) for p in s.points],
            "group_id": s.group_id,
            "description": s.description,
            "is_difficult": s.is_difficult,
            "shape_type": s.shape_type.name if isinstance(s.shape_type, ShapeType) else s.shape_type,
            "flags": s.flags,
            "attributes": s.attributes,
            "kie_linking": s.kie_linking,
        }
        if ShapeType.ROTATION == s.shape_type:
            info["direction"] = s.direction
        data.update(info)

        return data

    # Get current shapes
    # Excluding auto labeling special shapes
    shapes = [
        format_shape(item.shape())
        for item in CORE.Object.label_list_widget
        if item.shape().label not in [AutoLabelEditMode.OBJECT.value, AutoLabelEditMode.ADD.value, AutoLabelEditMode.REMOVE.value]
    ]
    flags = {}
    for i in range(CORE.Object.flag_widget.count()):
        item = CORE.Object.flag_widget.item(i)
        key = item.text()
        flag = item.checkState() == Qt.Checked
        flags[key] = flag
    try:
        image_path = os.path.relpath(CORE.Variable.image_path, os.path.dirname(filename))
        image_data = CORE.Variable.image_data if CORE.Variable.settings.get("store_data", False) else None
        if os.path.dirname(filename) and not os.path.exists(os.path.dirname(filename)):
            os.makedirs(os.path.dirname(filename))
        label_file.save(
            filename=filename,
            shapes=shapes,
            image_path=image_path,
            image_data=image_data,
            image_height=CORE.Variable.image.height(),
            image_width=CORE.Variable.image.width(),
            other_data=CORE.Variable.other_data,
            flags=flags,
        )
        CORE.Variable.label_file = label_file
        items = CORE.Object.info_file_list_widget.findItems(CORE.Variable.image_path, Qt.MatchExactly)
        if len(items) > 0:
            if len(items) != 1:
                logger.error("There are duplicate files.")
                raise RuntimeError("There are duplicate files.")
            items[0].setCheckState(Qt.Checked)
        return True
    except LabelFileError as e:
        QtWidgets.QMessageBox.critical(
            CORE.Object.main_window,
            "Error",
            f"Error saving label data: <b>{e}</b>",
            QtWidgets.QMessageBox.Ok
        )
        logger.error(f"Error saving label data: {e}")
        return False


def save_file():
    if not CORE.Variable.image or CORE.Variable.image.isNull():
        QtWidgets.QMessageBox.critical(
            CORE.Object.main_window,
            "Error",
            "Cannot save empty image",
            QtWidgets.QMessageBox.Ok
        )
        logger.error(f"Cannot save empty image: {CORE.Variable.current_file_full_path}")
        return
    if CORE.Variable.label_file:
        save_label_file(CORE.Variable.label_file.filename)
    else:
        save_label_file(SaveFileDialog().get_save_file_name())


def save_file_as():
    if not CORE.Variable.image or CORE.Variable.image.isNull():
        QtWidgets.QMessageBox.critical(
            CORE.Object.main_window,
            "Error",
            "Cannot save empty image",
            QtWidgets.QMessageBox.Ok
        )
        return
    save_label_file(SaveFileDialog().get_save_file_name())


def load_file(filename: str = None):
    CORE.Variable.settings.save()

    # For auto labeling
    # TODO self.clear_auto_labeling_marks()
    # TODO self.inform_next_files(filename)

    # Changing file_list_widget loads file
    if filename in CORE.Variable.image_list and CORE.Object.info_file_list_widget.currentRow() != CORE.Variable.image_list.index(filename):
        CORE.Object.info_file_list_widget.setCurrentRow(CORE.Variable.image_list.index(filename))
        CORE.Object.info_file_list_widget.repaint()
        return False

    reset_state()
    CORE.Object.canvas.setEnabled(False)
    if filename is None:
        filename = CORE.Variable.settings.get("filename", "")
    filename = str(filename)
    if not QtCore.QFile.exists(filename):
        QtWidgets.QMessageBox.critical(
            CORE.Object.main_window,
            "Error opening file",
            f"No such file: <b>{filename}</b>",
            QtWidgets.QMessageBox.Ok
        )
        logger.error(f"Error opening file: No such file: {filename}")
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
            QtWidgets.QMessageBox.critical(
                CORE.Object.main_window,
                "Error opening file",
                f"<p><b>{e}</b></p><p>Make sure <i>{label_file}</i> is a valid label file.",
                QtWidgets.QMessageBox.Ok
            )
            logger.error(f"Error reading {label_file}")
            CORE.Object.status_bar.showMessage(f"Error reading {label_file}")
            return False
        CORE.Variable.image_data = CORE.Variable.label_file.image_data
        CORE.Variable.image_path = os.path.join(os.path.dirname(label_file), CORE.Variable.label_file.image_path)
        CORE.Variable.other_data = CORE.Variable.label_file.other_data

        CORE.Object.item_description.textChanged.disconnect()
        CORE.Object.item_description.setPlainText(CORE.Variable.other_data.get("image_description", ""))
        CORE.Object.item_description.textChanged.connect(on_item_description_change)
    else:
        CORE.Variable.image_data = LabelFile.load_image_file(filename)
        if CORE.Variable.image_data:
            CORE.Variable.image_path = filename
        CORE.Variable.label_file = None
    handling_image = QtGui.QImage.fromData(CORE.Variable.image_data)

    if handling_image.isNull():
        formats = [f"*.{fmt.data().decode()}" for fmt in QtGui.QImageReader.supportedImageFormats()]
        QtWidgets.QMessageBox.critical(
            CORE.Object.main_window,
            "Error opening file",
            f"<p>Make sure <i>{filename}</i> is a valid image file.<br/>Supported image formats: {','.join(formats)}</p>",
            QtWidgets.QMessageBox.Ok
        )
        logger.error(f"Error reading {filename}")
        CORE.Object.status_bar.showMessage(f"Error reading {filename}")
        return False
    CORE.Variable.image = handling_image
    CORE.Variable.current_file_full_path = filename
    prev_shapes = []
    if CORE.Variable.settings.get("keep_prev", False):
        prev_shapes = CORE.Object.canvas.shapes
    CORE.Object.canvas.load_pixmap(QtGui.QPixmap.fromImage(handling_image))
    flags = {k: False for k in CORE.Variable.image_flags or []}
    if CORE.Variable.label_file:
        CORE.Object.canvas.load_labels(CORE.Variable.label_file.shapes)
        if CORE.Variable.label_file.flags is not None:
            flags.update(CORE.Variable.label_file.flags)
    load_flags(flags)

    if CORE.Variable.settings.get("keep_prev", False) and CORE.Object.canvas.is_no_shape:
        system.load_shapes(prev_shapes, replace=False)
        set_dirty()
    else:
        set_clean()

    CORE.Object.canvas.setEnabled(True)

    # set zoom values
    is_initial_load = not CORE.Object.canvas.zoom_history
    if CORE.Variable.current_file_full_path in CORE.Object.canvas.zoom_history:
        zoom_mode = CORE.Object.canvas.zoom_history[CORE.Variable.current_file_full_path]
        CORE.Object.canvas.zoom_mode = zoom_mode[0]
        set_zoom(zoom_mode[1])
    elif is_initial_load or not CORE.Variable.settings.get("keep_prev_scale", False):
        adjust_scale(initial=True)

    # set scroll values
    for orientation in CORE.Object.canvas.scroll_values:
        if CORE.Variable.current_file_full_path in CORE.Object.canvas.scroll_values[orientation]:
            set_scroll_value(orientation, CORE.Object.canvas.scroll_values[orientation][CORE.Variable.current_file_full_path])

    # set brightness contrast values
    dialog = BrightnessContrastDialog(img_data_to_pil(CORE.Variable.image_data))
    brightness, contrast = CORE.Variable.brightness_contrast_map.get(CORE.Variable.current_file_full_path, (None, None))
    if CORE.Variable.settings.get("keep_prev_brightness", False) and CORE.Variable.recent_files:
        brightness, _ = CORE.Variable.brightness_contrast_map.get(CORE.Variable.recent_files[0], (None, None))
    if CORE.Variable.settings.get("keep_prev_contrast", False) and CORE.Variable.recent_files:
        _, contrast = CORE.Variable.brightness_contrast_map.get(CORE.Variable.recent_files[0], (None, None))
    if brightness is not None:
        dialog.slider_brightness.setValue(brightness)
    if contrast is not None:
        dialog.slider_contrast.setValue(contrast)
    CORE.Variable.brightness_contrast_map[CORE.Variable.current_file_full_path] = (brightness, contrast)
    if brightness is not None or contrast is not None:
        dialog.on_new_value()
    paint_canvas()
    add_recent_file(CORE.Variable.current_file_full_path)
    toggle_zoom_related_action(True)
    toggle_load_related_action(True)
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
        if CORE.Object.info_file_list_widget.item(i).checkState() == Qt.Checked:
            CORE.Variable.current_file_full_path = CORE.Variable.image_list[i]
            if CORE.Variable.current_file_full_path and need_load:
                load_file(CORE.Variable.current_file_full_path)
            break


def open_next_image(need_load=True) -> None:
    """
    Open next image to be labeled
    """
    if QtWidgets.QApplication.keyboardModifiers() == (Qt.ControlModifier | Qt.ShiftModifier):
        open_labeled_image(CORE.Object.info_file_list_widget.count(), 1, need_load)
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
    if QtWidgets.QApplication.keyboardModifiers() == (Qt.ControlModifier | Qt.ShiftModifier):
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
        default_open_dir_path = os.path.dirname(CORE.Variable.current_file_full_path) if CORE.Variable.current_file_full_path else "."

    target_dir_path = str(
        QtWidgets.QFileDialog.getExistingDirectory(
            CORE.Object.main_window,
            f"{Constants.APP_NAME} - Open Directory",
            default_open_dir_path,
            QtWidgets.QFileDialog.ShowDirsOnly | QtWidgets.QFileDialog.DontResolveSymlinks,
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
    CORE.Object.info_file_list_widget.clear()
    for filename in walkthrough_files_in_dir(dir_path):
        if pattern and pattern not in filename:
            continue
        label_file = os.path.splitext(filename)[0] + ".json"
        if CORE.Variable.output_dir:
            label_file = os.path.join(CORE.Variable.output_dir, os.path.basename(label_file))
        item = QtWidgets.QListWidgetItem(filename)
        item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
        if QtCore.QFile.exists(label_file) and LabelFile.is_label_file(label_file):
            item.setCheckState(Qt.Checked)
        else:
            item.setCheckState(Qt.Unchecked)
        CORE.Object.info_file_list_widget.addItem(item)
    open_next_image(need_load=need_load)


def open_video():
    if not utils.qt_utils.may_continue():
        return

    default_open_video_path = os.path.dirname(CORE.Variable.current_file_full_path) if CORE.Variable.current_file_full_path else "."
    source_video_path, _ = QtWidgets.QFileDialog.getOpenFileName(
        CORE.Object.main_window,
        f"{Constants.APP_NAME} - Open Video file",
        default_open_video_path,
        "*.asf *.avi *.m4v *.mkv *.mov *.mp4 *.mpeg *.mpg *.ts *.wmv",
    )

    # Check if the path contains Chinese characters
    if has_chinese(source_video_path):
        QtWidgets.QMessageBox.warning(
            CORE.Object.main_window,
            "Warning",
            "File path cannot contains Chinese characters",
            QtWidgets.QMessageBox.Ok,
        )
        return

    if os.path.exists(source_video_path):
        target_dir_path = extract_frames_from_video(source_video_path)
        load_image_folder(target_dir_path)


def add_recent_file(filename: str):
    if filename in CORE.Variable.recent_files:
        CORE.Variable.recent_files.remove(filename)
    elif len(CORE.Variable.recent_files) > 10:
        CORE.Variable.recent_files.pop()
    CORE.Variable.recent_files.insert(0, filename)


def update_file_menu():
    CORE.Action.open_recent.clear()
    files = [f for f in CORE.Variable.recent_files if f != CORE.Variable.current_file_full_path and os.path.exists(f)]
    for i, f in enumerate(files):
        icon = utils.qt_utils.new_icon("labels")
        action = QtWidgets.QAction(icon, "&%d %s" % (i + 1, QtCore.QFileInfo(f).fileName()), CORE.Action.open_recent)
        action.triggered.connect(functools.partial(lambda x: load_file(x) if utils.qt_utils.may_continue() else None, f))
        CORE.Action.open_recent.addAction(action)


def change_output_dir():
    default_output_dir = CORE.Variable.output_dir
    if default_output_dir is None and CORE.Variable.current_file_full_path:
        default_output_dir = os.path.dirname(CORE.Variable.current_file_full_path)
    if default_output_dir is None:
        default_output_dir = os.path.dirname(str(CORE.Variable.current_file_full_path)) if CORE.Variable.current_file_full_path else "."

    output_dir = QtWidgets.QFileDialog.getExistingDirectory(
        CORE.Object.main_window,
        f"{Constants.APP_NAME} - Save/Load Annotations in Directory",
        str(default_output_dir),
        QtWidgets.QFileDialog.ShowDirsOnly | QtWidgets.QFileDialog.DontResolveSymlinks,
    )
    output_dir = str(output_dir)
    if not output_dir:
        return

    CORE.Variable.output_dir = output_dir

    CORE.Object.status_bar.showMessage("Change Annotations Dir. Annotations will be saved/loaded in {CORE.Variable.output_dir}")

    load_image_folder(CORE.Variable.last_open_dir_path, need_load=False)

    if CORE.Variable.current_file_full_path in CORE.Variable.image_list:
        CORE.Object.info_file_list_widget.setCurrentRow(CORE.Variable.image_list.index(CORE.Variable.current_file_full_path))
        CORE.Object.info_file_list_widget.repaint()


def get_label_file():
    if CORE.Variable.current_file_full_path.lower().endswith(".json"):
        label_file = CORE.Variable.current_file_full_path
    else:
        label_file = os.path.splitext(CORE.Variable.current_file_full_path)[0] + ".json"
    return label_file


def get_image_file():
    if not CORE.Variable.current_file_full_path.lower().endswith(".json"):
        image_file = CORE.Variable.current_file_full_path
    else:
        image_file = CORE.Variable.image_path
    return image_file


def delete_label_file():
    answer = QtWidgets.QMessageBox.warning(
        CORE.Object.main_window,
        "Attention",
        "Confirm to permanently delete this label file?",
        QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
        QtWidgets.QMessageBox.No
    )
    if answer != QtWidgets.QMessageBox.Yes:
        return

    label_file = get_label_file()
    if os.path.exists(label_file):
        os.remove(label_file)
        logger.info("Label file is removed: %s", label_file)

        item = CORE.Object.info_file_list_widget.currentItem()
        item.setCheckState(Qt.Unchecked)

        filename = CORE.Variable.current_file_full_path
        reset_state()
        CORE.Variable.current_file_full_path = filename
        if CORE.Variable.current_file_full_path:
            load_file(CORE.Variable.current_file_full_path)


def delete_image_file():
    if len(CORE.Variable.image_list) <= 0:
        return

    answer = QtWidgets.QMessageBox.warning(
        CORE.Object.main_window,
        "Attention",
        "Confirm to permanently delete this image file?",
        QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
        QtWidgets.QMessageBox.No
    )
    if answer != QtWidgets.QMessageBox.Yes:
        return

    image_file = get_image_file()
    if os.path.exists(image_file):
        image_path, image_name = os.path.split(image_file)
        os.remove(image_file)

        label_dir_path = os.path.dirname(CORE.Variable.current_file_full_path)
        if CORE.Variable.output_dir:
            label_dir_path = CORE.Variable.output_dir
        label_name = os.path.splitext(image_name)[0] + ".json"
        label_file = os.path.join(label_dir_path, label_name)
        if os.path.exists(label_file):
            os.remove(label_file)
            logger.info("Label file is removed: %s", image_file)

        if CORE.Variable.current_file_full_path is None:
            filename = CORE.Variable.image_list[0]
        else:
            current_index = CORE.Variable.image_list.index(CORE.Variable.current_file_full_path)
            if current_index + 1 < len(CORE.Variable.image_list):
                filename = CORE.Variable.image_list[current_index + 1]
            else:
                filename = CORE.Variable.image_list[0]

        reset_state()
        if os.path.isfile(image_path):
            image_path = os.path.dirname(image_path)
        load_image_folder(image_path)

        CORE.Variable.current_file_full_path = filename
        if CORE.Variable.current_file_full_path:
            load_file(CORE.Variable.current_file_full_path)


def close_file():
    if not utils.qt_utils.may_continue():
        return
    reset_state()
    set_clean()
    toggle_zoom_related_action(False)
    toggle_load_related_action(False)
    CORE.Object.canvas.setEnabled(False)
    CORE.Action.save_file_as.setEnabled(False)
