import json
import os
import shutil

import cv2
import numpy as np
from PyQt5 import QtWidgets, QtCore

from core.configs.core import CORE
from core.dto.enums import ShapeType
from core.services.system import show_critical_message
from core.views.modules.chat_tab import ChatTab
from core.views.modules.object_detection_tab import ObjectDetectionTab
from core.views.modules.segmentation_tab import SegmentationTab


def save_crop_image():
    if not CORE.Variable.current_file_full_path:
        return
    image_file_list, label_dir_path = [], ""
    if not CORE.Variable.image_list and CORE.Variable.current_file_full_path:
        image_file_list = [CORE.Variable.current_file_full_path]
        dir_path, filename = os.path.split(CORE.Variable.current_file_full_path)
        label_file = os.path.join(dir_path, os.path.splitext(filename)[0] + ".json")
        if os.path.exists(label_file):
            label_dir_path = dir_path
    elif CORE.Variable.image_list and not CORE.Variable.output_dir and CORE.Variable.current_file_full_path:
        image_file_list = CORE.Variable.image_list
        label_dir_path = os.path.dirname(CORE.Variable.current_file_full_path)
    if CORE.Variable.output_dir:
        label_dir_path = CORE.Variable.output_dir
    save_path = os.path.join(os.path.dirname(CORE.Variable.current_file_full_path), "..", "CropImages")
    if os.path.exists(save_path):
        shutil.rmtree(save_path)

    progress_dialog = QtWidgets.QProgressDialog(
        "Processing...",
        "Cancel",
        0,
        len(image_file_list),
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
    label_to_count = {}
    try:
        for i, image_file in enumerate(image_file_list):
            image_name = os.path.basename(image_file)
            label_name = os.path.splitext(image_name)[0] + ".json"
            label_file = os.path.join(label_dir_path, label_name)
            if not os.path.exists(label_file):
                continue

            with open(label_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            shapes = data["shapes"]
            for shape in shapes:
                label = shape["label"]
                points = shape["points"]
                shape_type = shape["shape_type"]
                if shape_type not in (ShapeType.RECTANGLE.name, ShapeType.POLYGON.name, ShapeType.ROTATION.name):
                    continue
                elif (ShapeType.POLYGON == shape_type and len(points) < 3) or (ShapeType.ROTATION == shape_type and len(points) != 4) or (ShapeType.RECTANGLE == shape_type and len(points) != 4):
                    progress_dialog.close()
                    show_critical_message("Error", f"Existing invalid shape in {label_file}", trace=False)
                    return

                points = np.array(points).astype(np.int32)
                x, y, w, h = cv2.boundingRect(points)
                min_x = int(x)
                min_y = int(y)
                max_x = int(w) + min_x
                max_y = int(h) + min_y

                dest_path = os.path.join(save_path, label)
                if not os.path.exists(dest_path):
                    label_to_count[label] = 0
                    os.makedirs(dest_path)
                else:
                    label_to_count[label] += 1

                image = cv2.imread(image_file)
                height, width = image.shape[:2]
                min_x, min_y, max_x, max_y = map(int, [min_x, min_y, max_x, max_y])
                min_x = max(0, min(min_x, width))
                min_y = max(0, min(min_y, height))
                max_x = max(min_x, min(max_x, width))
                max_y = max(min_y, min(max_y, height))
                crop_image = image[min_y:max_y, min_x:max_x]
                dest_file = os.path.join(dest_path, f"{label_to_count[label]}-{shape_type}.jpg")
                cv2.imencode(".jpg", crop_image)[1].tofile(dest_file)
            # Update progress bar
            progress_dialog.setValue(i)
            if progress_dialog.wasCanceled():
                break
        # Hide the progress dialog after processing is done
        progress_dialog.close()

        # Show success message
        save_path = os.path.realpath(save_path)
        QtWidgets.QMessageBox.information(
            CORE.Object.main_window,
            "Success",
            f"Cropping completed successfully!\nCropped images have been saved to:\n{save_path}",
            QtWidgets.QMessageBox.Ok
        )

    except Exception:
        progress_dialog.close()
        show_critical_message("Error", "Error occurred while saving cropped image.")


def toggle_object_detection():
    if CORE.Variable.use_object_detection:
        CORE.Object.tab_widget.removeTab(CORE.Object.tab_widget.indexOf(CORE.Object.object_detection_tab_widget))
        CORE.Object.object_detection_button.setDown(False)
        CORE.Variable.use_object_detection = False
        for name in CORE.Object.model_manager.active_od_models:
            CORE.Object.model_manager.model_dict[name].model.unload()
    else:
        if CORE.Object.object_detection_tab_widget is None:
            CORE.Object.object_detection_tab_widget = ObjectDetectionTab()
        CORE.Object.tab_widget.addTab(CORE.Object.object_detection_tab_widget, "Object Detection")
        CORE.Object.tab_widget.setCurrentIndex(CORE.Object.tab_widget.count() - 1)
        CORE.Object.tab_widget.tabBar().setTabButton(CORE.Object.tab_widget.count() - 1, QtWidgets.QTabBar.RightSide, None)
        CORE.Object.object_detection_button.setDown(True)
        CORE.Variable.use_object_detection = True


def toggle_segmentation():
    if CORE.Variable.use_segmentation:
        CORE.Object.tab_widget.removeTab(CORE.Object.tab_widget.indexOf(CORE.Object.segmentation_tab_widget))
        CORE.Object.segmentation_button.setDown(False)
        CORE.Variable.use_segmentation = False
        for name in CORE.Object.model_manager.active_seg_models:
            CORE.Object.model_manager.model_dict[name].model.unload()
    else:
        if CORE.Object.segmentation_tab_widget is None:
            CORE.Object.segmentation_tab_widget = SegmentationTab()
        CORE.Object.tab_widget.addTab(CORE.Object.segmentation_tab_widget, "Segmentation")
        CORE.Object.tab_widget.setCurrentIndex(CORE.Object.tab_widget.count() - 1)
        CORE.Object.tab_widget.tabBar().setTabButton(CORE.Object.tab_widget.count() - 1, QtWidgets.QTabBar.RightSide, None)
        CORE.Object.segmentation_button.setDown(True)
        CORE.Variable.use_segmentation = True


def toggle_chat():
    if CORE.Variable.use_chat:
        CORE.Object.tab_widget.removeTab(CORE.Object.tab_widget.indexOf(CORE.Object.chat_tab_widget))
        CORE.Object.nlp_button.setDown(False)
        CORE.Variable.use_chat = False
    else:
        if CORE.Object.chat_tab_widget is None:
            CORE.Object.chat_tab_widget = ChatTab()
        CORE.Object.tab_widget.addTab(CORE.Object.chat_tab_widget, "Labeling Chat")
        CORE.Object.tab_widget.setCurrentIndex(CORE.Object.tab_widget.count() - 1)
        CORE.Object.tab_widget.tabBar().setTabButton(CORE.Object.tab_widget.count() - 1, QtWidgets.QTabBar.RightSide, None)
        CORE.Object.nlp_button.setDown(True)
        CORE.Variable.use_chat = True
