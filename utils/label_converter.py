import configparser
import json
import math
import os
import os.path as osp
import pathlib
from datetime import date
from itertools import chain
from typing import Tuple

import cv2
import jsonlines
import numpy as np
import yaml
from PIL import Image
from _elementtree import Element
from defusedxml import ElementTree

from core.configs.constants import Constants
from core.dto.enums import ShapeType
from utils.function import is_possible_rectangle
from utils.logger import logger


class LabelConverter:
    def __init__(self, classes_file=None, pose_cfg_file=None):
        self.classes = []
        self.custom_data = {}
        if classes_file:
            with open(classes_file, "r", encoding="utf-8") as f:
                self.classes = f.read().splitlines()
            logger.info(f"Loading classes: {self.classes}")
        self.pose_classes = {}
        if pose_cfg_file:
            with open(pose_cfg_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                self.has_visible = data['has_visible']
                for class_name, keypoint_name in data['classes'].items():
                    self.pose_classes[class_name] = keypoint_name

    def reset(self):
        self.custom_data = {
            "version": Constants.APP_VERSION,
            "flags": {},
            "shapes": [],
            "imagePath": "",
            "imageData": None,
            "imageHeight": -1,
            "imageWidth": -1
        }

    @staticmethod
    def calculate_rotation_theta(points) -> float:
        x1, y1 = points[0]
        x2, y2 = points[1]

        # Calculate one of the diagonal vectors (after rotation)
        diagonal_vector_x = x2 - x1
        diagonal_vector_y = y2 - y1

        # Calculate the rotation angle in radians
        rotation_angle = math.atan2(diagonal_vector_y, diagonal_vector_x)

        # Convert radians to degrees
        rotation_angle_degrees = math.degrees(rotation_angle)

        if rotation_angle_degrees < 0:
            rotation_angle_degrees += 360

        return rotation_angle_degrees / 360 * (2 * math.pi)

    @staticmethod
    def calculate_polygon_area(segmentation) -> float:
        x, y = [], []
        for i in range(len(segmentation)):
            if i % 2 == 0:
                x.append(segmentation[i])
            else:
                y.append(segmentation[i])
        area = 0.5 * np.abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))
        return float(area)

    @staticmethod
    def get_image_size(image_file) -> Tuple[int, int]:
        with Image.open(image_file) as img:
            width, height = img.size
            return width, height

    @staticmethod
    def get_min_enclosing_bbox(segmentation) -> list:
        if not segmentation:
            return []
        polygon_points = [(segmentation[i], segmentation[i + 1]) for i in range(0, len(segmentation), 2)]
        x_coords, y_coords = zip(*polygon_points)
        x_min = min(x_coords)
        y_min = min(y_coords)
        x_max = max(x_coords)
        y_max = max(y_coords)
        bbox_width = x_max - x_min
        bbox_height = y_max - y_min
        return [x_min, y_min, bbox_width, bbox_height]

    @staticmethod
    def get_contours_and_labels(mask, mapping_table, epsilon_factor=0.001):
        results = []
        input_type = mapping_table["type"]
        mapping_color = mapping_table["colors"]

        if input_type == "grayscale":
            color_to_label = {v: k for k, v in mapping_color.items()}
            binary_img = cv2.imread(mask, cv2.IMREAD_GRAYSCALE)
            # use the different color_value to find the sub-region for each class
            for color_value in np.unique(binary_img):
                class_name = color_to_label.get(color_value, "Unknown")
                label_map = (binary_img == color_value).astype(np.uint8)

                contours, _ = cv2.findContours(label_map, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                for contour in contours:
                    epsilon = epsilon_factor * cv2.arcLength(contour, True)
                    approx = cv2.approxPolyDP(contour, epsilon, True)
                    if len(approx) < 5:
                        continue

                    points = []
                    for point in approx:
                        x, y = point[0].tolist()
                        points.append([x, y])
                    result_item = {"points": points, "label": class_name}
                    results.append(result_item)
        elif input_type == "rgb":
            color_to_label = {tuple(color): label for label, color in mapping_color.items()}
            rgb_img = cv2.imread(mask)
            hsv_img = cv2.cvtColor(rgb_img, cv2.COLOR_BGR2HSV)

            _, binary_img = cv2.threshold(hsv_img[:, :, 1], 0, 255, cv2.THRESH_BINARY)
            contours, _ = cv2.findContours(binary_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            for contour in contours:
                epsilon = epsilon_factor * cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, epsilon, True)
                if len(approx) < 5:
                    continue

                x, y, w, h = cv2.boundingRect(contour)
                center = (int(x + w / 2), int(y + h / 2))
                rgb_color = rgb_img[center[1], center[0]].tolist()
                label = color_to_label.get(tuple(rgb_color[::-1]), "Unknown")

                points = []
                for point in approx:
                    x, y = point[0].tolist()
                    points.append([x, y])

                result_item = {"points": points, "label": label}
                results.append(result_item)
        return results

    @staticmethod
    def get_coco_data():
        coco_data = {
            "info": {
                "year": 2023,
                "version": Constants.APP_VERSION,
                "description": "COCO Label Conversion",
                "contributor": "CVHub",
                "url": "https://github.com/CVHub520/X-AnyLabeling",
                "date_created": str(date.today()),
            },
            "licenses": [
                {
                    "id": 1,
                    "url": "https://www.gnu.org/licenses/gpl-3.0.html",
                    "name": "GNU GENERAL PUBLIC LICENSE Version 3",
                }
            ],
            "categories": [],
            "images": [],
            "annotations": [],
        }
        return coco_data

    def calculate_normalized_bbox(self, poly, img_w, img_h):
        """
        Calculate the minimum bounding box for a set of four points and return the YOLO format rectangle representation (normalized).

        Args:
        - poly (list): List of four points [(x1, y1), (x2, y2), (x3, y3), (x4, y4)].
        - img_w (int): Width of the corresponding image.
        - img_h (int): Height of the corresponding image.

        Returns:
        - tuple: Tuple representing the YOLO format rectangle in xywh_center form (all normalized).
        """
        x_min, y_min, x_max, y_max = self.calculate_bounding_box(poly)
        x_center = (x_min + x_max) / (2 * img_w)
        y_center = (y_min + y_max) / (2 * img_h)
        width = (x_max - x_min) / img_w
        height = (y_max - y_min) / img_h
        return x_center, y_center, width, height

    @staticmethod
    def calculate_bounding_box(poly):
        """
        Calculate the minimum bounding box for a set of four points.

        Args:
        - poly (list): List of four points [(x1, y1), (x2, y2), (x3, y3), (x4, y4)].

        Returns:
        - tuple: Tuple representing the bounding box (x_min, y_min, x_max, y_max).
        """
        x_vals, y_vals = zip(*poly)
        return min(x_vals), min(y_vals), max(x_vals), max(y_vals)

    @staticmethod
    def gen_quad_from_poly(poly):
        """
        Generate min area quad from poly.
        """
        point_num = poly.shape[0]
        min_area_quad = np.zeros((4, 2), dtype=np.float32)
        rect = cv2.minAreaRect(poly.astype(np.int32))
        box = np.array(cv2.boxPoints(rect))

        first_point_idx = 0
        min_dist = 1e4
        for i in range(4):
            dist = (
                    np.linalg.norm(box[(i + 0) % 4] - poly[0])
                    + np.linalg.norm(box[(i + 1) % 4] - poly[point_num // 2 - 1])
                    + np.linalg.norm(box[(i + 2) % 4] - poly[point_num // 2])
                    + np.linalg.norm(box[(i + 3) % 4] - poly[-1])
            )
            if dist < min_dist:
                min_dist = dist
                first_point_idx = i
        for i in range(4):
            min_area_quad[i] = box[(first_point_idx + i) % 4]

        bbox_new = min_area_quad.tolist()
        bbox = []

        for box in bbox_new:
            box = list(map(int, box))
            bbox.append(box)

        return bbox

    @staticmethod
    def get_rotate_crop_image(img, points):
        # Use Green's theory to judge clockwise or counterclockwise
        d = 0.0
        for index in range(-1, 3):
            d += -0.5 * (points[index + 1][1] + points[index][1]) * (points[index + 1][0] - points[index][0])
        if d < 0:  # counterclockwise
            tmp = np.array(points)
            points[1], points[3] = tmp[3], tmp[1]

        try:
            img_crop_width = int(max(np.linalg.norm(points[0] - points[1]), np.linalg.norm(points[2] - points[3])))
            img_crop_height = int(max(np.linalg.norm(points[0] - points[3]), np.linalg.norm(points[1] - points[2])))
            pts_std = np.float32([
                [0, 0],
                [img_crop_width, 0],
                [img_crop_width, img_crop_height],
                [0, img_crop_height],
            ])
            M = cv2.getPerspectiveTransform(points, pts_std)
            dst_img = cv2.warpPerspective(
                img,
                M,
                (img_crop_width, img_crop_height),
                borderMode=cv2.BORDER_REPLICATE,
                flags=cv2.INTER_CUBIC,
            )
            dst_img_height, dst_img_width = dst_img.shape[0:2]
            if dst_img_height * 1.0 / dst_img_width >= 1.5:
                dst_img = np.rot90(dst_img)
            return dst_img
        except Exception as e:
            print(e)

    def yolo_obb_to_custom(self, input_file, output_file, image_file):
        self.reset()
        with open(input_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
        img_w, img_h = self.get_image_size(image_file)
        for line in lines:
            line = line.strip().split(" ")
            class_index = int(line[0])
            label = self.classes[class_index]
            shape_type = ShapeType.ROTATION.name
            # Extracting coordinates from YOLO format
            x0, y0, x1, y1, x2, y2, x3, y3 = map(float, line[1:])
            # Rescaling coordinates to image size
            x0, y0, x1, y1, x2, y2, x3, y3 = (
                x0 * img_w,
                y0 * img_h,
                x1 * img_w,
                y1 * img_h,
                x2 * img_w,
                y2 * img_h,
                x3 * img_w,
                y3 * img_h,
            )
            # Creating points in the custom format
            points = [[x0, y0], [x1, y1], [x2, y2], [x3, y3]]
            shape = {
                "label": label,
                "shape_type": shape_type,
                "flags": {},
                "points": points,
                "group_id": None,
                "description": None,
                "is_difficult": False,
                "direction": self.calculate_rotation_theta(points),
                "attributes": {},
            }
            self.custom_data["shapes"].append(shape)
        self.custom_data["imagePath"] = osp.basename(image_file)
        self.custom_data["imageHeight"] = img_h
        self.custom_data["imageWidth"] = img_w
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(self.custom_data, f, indent=2, ensure_ascii=False)

    def yolo_pose_to_custom(self, input_file, output_file, image_file):
        self.reset()
        with open(input_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
        img_w, img_h = self.get_image_size(image_file)
        classes = list(self.pose_classes.keys())
        for i, line in enumerate(lines):
            line = line.strip().split(" ")
            class_index = int(line[0])
            label = classes[class_index]
            # Add rectangle info
            cx = float(line[1])
            cy = float(line[2])
            nw = float(line[3])
            nh = float(line[4])
            x_min = int((cx - nw / 2) * img_w)
            y_min = int((cy - nh / 2) * img_h)
            x_max = int((cx + nw / 2) * img_w)
            y_max = int((cy + nh / 2) * img_h)
            points = [
                [x_min, y_min],
                [x_max, y_min],
                [x_max, y_max],
                [x_min, y_max],
            ]
            shape = {
                "label": label,
                "shape_type": ShapeType.RECTANGLE.name,
                "flags": {},
                "points": points,
                "group_id": i,
                "description": None,
                "is_difficult": False,
                "attributes": {},
            }
            self.custom_data["shapes"].append(shape)
            # Add key points info
            key_point_name = self.pose_classes[label]
            key_points = line[5:]
            interval = 3 if self.has_visible else 2
            for j in range(0, len(key_points), interval):
                x = float(key_points[j]) * img_w
                y = float(key_points[j + 1]) * img_h
                flag = int(key_points[j + 2])
                if (x == 0 and y == 0) or flag == 0:
                    continue
                if interval == 3 and flag == 1:
                    is_difficult = True
                else:
                    is_difficult = False
                shape = {
                    "label": key_point_name[j // interval],
                    "shape_type": ShapeType.POINT.name,
                    "flags": {},
                    "points": [[x, y]],
                    "group_id": i,
                    "description": None,
                    "is_difficult": is_difficult,
                    "attributes": {},
                }
                self.custom_data["shapes"].append(shape)

        self.custom_data["imagePath"] = osp.basename(image_file)
        self.custom_data["imageHeight"] = img_h
        self.custom_data["imageWidth"] = img_w
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(self.custom_data, f, indent=2, ensure_ascii=False)

    def yolo_to_custom(self, input_file, output_file, image_file, mode):
        self.reset()
        with open(input_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
        img_w, img_h = self.get_image_size(image_file)
        image_size = np.array([img_w, img_h], np.float64)
        for line in lines:
            line = line.strip().split(" ")
            class_index = int(line[0])
            label = self.classes[class_index]
            if mode == "hbb":
                shape_type = ShapeType.RECTANGLE.name
                cx = float(line[1])
                cy = float(line[2])
                nw = float(line[3])
                nh = float(line[4])
                x_min = int((cx - nw / 2) * img_w)
                y_min = int((cy - nh / 2) * img_h)
                x_max = int((cx + nw / 2) * img_w)
                y_max = int((cy + nh / 2) * img_h)
                points = [
                    [x_min, y_min],
                    [x_max, y_min],
                    [x_max, y_max],
                    [x_min, y_max],
                ]
            elif mode == "seg":
                shape_type = ShapeType.POLYGON.name
                points, masks = [], line[1:]
                for x, y in zip(masks[0::2], masks[1::2]):
                    point = [np.float64(x), np.float64(y)]
                    point = np.array(point, np.float64) * image_size
                    points.append(point.tolist())
            else:
                logger.error(f"Unknown mode: {mode}")
                raise ValueError(f"Unknown mode: {mode}")
            shape = {
                "label": label,
                "shape_type": shape_type,
                "flags": {},
                "points": points,
                "group_id": None,
                "description": None,
                "is_difficult": False,
                "attributes": {},
            }
            self.custom_data["shapes"].append(shape)
        self.custom_data["imagePath"] = osp.basename(image_file)
        self.custom_data["imageHeight"] = img_h
        self.custom_data["imageWidth"] = img_w
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(self.custom_data, f, indent=2, ensure_ascii=False)

    def voc_to_custom(self, input_file, output_file, image_filename, mode):
        self.reset()

        tree = ElementTree.parse(input_file)
        root = tree.getroot()

        image_width = int(root.find("size/width").text)
        image_height = int(root.find("size/height").text)

        self.custom_data["imagePath"] = image_filename
        self.custom_data["imageHeight"] = image_height
        self.custom_data["imageWidth"] = image_width

        for obj in root.findall("object"):
            label = obj.find("name").text
            difficult = "0"
            if obj.find("is_difficult") is not None:
                difficult = str(obj.find("is_difficult").text)
            points = []
            if obj.find("polygon") is not None and mode == "polygon":
                num_points = len(obj.find("polygon")) // 2
                for i in range(1, num_points + 1):
                    x_tag = f"polygon/x{i}"
                    y_tag = f"polygon/y{i}"
                    x = float(obj.find(x_tag).text)
                    y = float(obj.find(y_tag).text)
                    points.append([x, y])
                shape_type = ShapeType.POLYGON.name
            elif obj.find("bndbox") is not None and mode in ["rectangle", "polygon"]:
                x_min = float(obj.find("bndbox/x_min").text)
                y_min = float(obj.find("bndbox/y_min").text)
                x_max = float(obj.find("bndbox/x_max").text)
                y_max = float(obj.find("bndbox/y_max").text)
                points = [
                    [x_min, y_min],
                    [x_max, y_min],
                    [x_max, y_max],
                    [x_min, y_max],
                ]
                shape_type = ShapeType.RECTANGLE.name
            else:
                logger.error(f"Unknown mode: {mode} or not find 'polygon or bndbox in obj: {obj}")
                raise ValueError(f"Unknown mode: {mode}")
            shape = {
                "label": label,
                "description": "",
                "points": points,
                "group_id": None,
                "difficult": bool(int(difficult)),
                "shape_type": shape_type,
                "flags": {},
            }

            self.custom_data["shapes"].append(shape)

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(self.custom_data, f, indent=2, ensure_ascii=False)

    def coco_to_custom(self, input_file, image_path, mode):
        with open(input_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not self.classes:
            for cat in data["categories"]:
                self.classes.append(cat["name"])

        total_info, label_info = {}, {}

        # map category_id to name
        for dic_info in data["categories"]:
            label_info[dic_info["id"]] = dic_info["name"]

        # map image_id to info
        for dic_info in data["images"]:
            total_info[dic_info["id"]] = {
                "imageWidth": dic_info["width"],
                "imageHeight": dic_info["height"],
                "imagePath": osp.basename(dic_info["file_name"]),
                "shapes": [],
            }

        for dic_info in data["annotations"]:
            difficult = bool(int(str(dic_info.get("ignore", "0"))))
            label = label_info[dic_info["category_id"]]

            if mode == "rectangle":
                shape_type = "rectangle"
                bbox = dic_info["bbox"]
                x_min = bbox[0]
                y_min = bbox[1]
                width = bbox[2]
                height = bbox[3]
                x_max = x_min + width
                y_max = y_min + height
                points = [
                    [x_min, y_min],
                    [x_max, y_min],
                    [x_max, y_max],
                    [x_min, y_max],
                ]
            elif mode == "polygon":
                shape_type = "polygon"
                segmentation = dic_info["segmentation"][0]
                if len(segmentation) < 6 or len(segmentation) % 2 != 0:
                    continue
                points = []
                for i in range(0, len(segmentation), 2):
                    points.append([segmentation[i], segmentation[i + 1]])
            else:
                logger.error(f"Unknown mode: {mode}")
                raise ValueError(f"Unknown mode: {mode}")

            shape = {
                "label": label,
                "shape_type": shape_type,
                "flags": {},
                "points": points,
                "group_id": None,
                "description": None,
                "difficult": difficult,
                "attributes": {},
            }

            total_info[dic_info["image_id"]]["shapes"].append(shape)

        for dic_info in total_info.values():
            self.reset()
            self.custom_data["shapes"] = dic_info["shapes"]
            self.custom_data["imagePath"] = dic_info["imagePath"]
            self.custom_data["imageHeight"] = dic_info["imageHeight"]
            self.custom_data["imageWidth"] = dic_info["imageWidth"]

            output_file = osp.join(image_path, osp.splitext(dic_info["imagePath"])[0] + ".json")
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(self.custom_data, f, indent=2, ensure_ascii=False)

    def dota_to_custom(self, input_file, output_file, image_file):
        self.reset()

        with open(input_file, "r", encoding="utf-8") as f:
            lines = f.readlines()

        image_width, image_height = self.get_image_size(image_file)

        for line in lines:
            line = line.strip().split(" ")
            x0, y0, x1, y1, x2, y2, x3, y3 = [float(i) for i in line[:8]]
            difficult = line[-1]
            points = [[x0, y0], [x1, y1], [x2, y2], [x3, y3]]
            shape = {
                "label": line[8],
                "description": None,
                "points": points,
                "group_id": None,
                "is_difficult": bool(int(difficult)),
                "direction": self.calculate_rotation_theta(points),
                "shape_type": ShapeType.ROTATION.name,
                "flags": {},
            }
            self.custom_data["shapes"].append(shape)

        self.custom_data["imagePath"] = osp.basename(image_file)
        self.custom_data["imageHeight"] = image_height
        self.custom_data["imageWidth"] = image_width

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(self.custom_data, f, indent=2, ensure_ascii=False)

    def mask_to_custom(self, input_file, output_file, image_file, mapping_table):
        self.reset()

        results = self.get_contours_and_labels(input_file, mapping_table)
        for result in results:
            shape = {
                "label": result["label"],
                "text": "",
                "points": result["points"],
                "group_id": None,
                "shape_type": ShapeType.POLYGON.name,
                "flags": {},
            }
            self.custom_data["shapes"].append(shape)

        image_width, image_height = self.get_image_size(image_file)
        self.custom_data["imagePath"] = os.path.basename(image_file)
        self.custom_data["imageHeight"] = image_height
        self.custom_data["imageWidth"] = image_width

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(self.custom_data, f, indent=2, ensure_ascii=False)

    def mot_to_custom(self, input_file, output_path, image_path):
        with open(input_file, "r", encoding="utf-8") as f:
            mot_data = [line.strip().split(',') for line in f]

        data_to_shape = {}
        for data in mot_data:
            frame_id = int(data[0])
            group_id = int(data[1])
            x_min = int(data[2])
            y_min = int(data[3])
            x_max = int(data[4]) + x_min
            y_max = int(data[5]) + y_min
            label = self.classes[int(data[7])]
            info = [label, x_min, y_min, x_max, y_max, group_id]
            if frame_id not in data_to_shape:
                data_to_shape[frame_id] = [info]
            else:
                data_to_shape[frame_id].append(info)

        file_list = os.listdir(image_path)
        for file_name in file_list:
            if file_name.endswith(".json"):
                continue

            self.reset()
            frame_id = int(osp.splitext(file_name.rsplit("-")[-1])[0])
            data = data_to_shape[frame_id]
            image_file = osp.join(image_path, file_name)
            image_width, image_height = self.get_image_size(image_file)

            shapes = []
            for d in data:
                label, x_min, y_min, x_max, y_max, group_id = d
                points = [
                    [x_min, y_min],
                    [x_max, y_min],
                    [x_max, y_max],
                    [x_min, y_max],
                ]
                shape = {
                    "label": label,
                    "description": None,
                    "points": points,
                    "group_id": group_id,
                    "is_difficult": False,
                    "direction": 0,
                    "shape_type": "rectangle",
                    "flags": {},
                }
                shapes.append(shape)

            image_path = file_name
            if output_path != image_path:
                image_path = osp.join(output_path, file_name)
            self.custom_data["imagePath"] = image_path
            self.custom_data["imageWidth"] = image_width
            self.custom_data["imageHeight"] = image_height
            self.custom_data["shapes"] = shapes

            output_file = osp.join(
                output_path, osp.splitext(file_name)[0] + ".json"
            )
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(self.custom_data, f, indent=2, ensure_ascii=False)

    def odvg_to_custom(self, input_file, output_path):
        # Load od.json or od.jsonl
        with jsonlines.open(input_file, 'r') as reader:
            od_data = list(reader)
        # Save custom info
        for data in od_data:
            self.reset()
            shapes = []
            for instance in data["detection"]["instance"]:
                x_min, y_min, x_max, y_max = instance["bbox"]
                points = [
                    [x_min, y_min],
                    [x_max, y_min],
                    [x_max, y_max],
                    [x_min, y_max],
                ]
                shape = {
                    "label": instance["category"],
                    "description": None,
                    "points": points,
                    "group_id": None,
                    "is_difficult": False,
                    "direction": 0,
                    "shape_type": "rectangle",
                    "flags": {},
                }
                shapes.append(shape)
            self.custom_data["imagePath"] = data["filename"]
            self.custom_data["imageHeight"] = data["height"]
            self.custom_data["imageWidth"] = data["width"]
            self.custom_data["shapes"] = shapes
            output_file = osp.join(output_path, osp.splitext(data["filename"])[0] + ".json")
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(self.custom_data, f, indent=2, ensure_ascii=False)

    def ppocr_to_custom(self, input_file, output_path, image_path, mode):
        if mode in ["rec", "kie"]:
            with open(input_file, "r", encoding="utf-8") as f:
                ocr_data = [line.strip().split('\t', 1) for line in f]

        for data in ocr_data:
            # init
            self.reset()

            # image
            filename = osp.basename(data[0])
            image_file = osp.join(image_path, filename)
            image_width, image_height = self.get_image_size(image_file)
            self.custom_data["imageHeight"] = image_height
            self.custom_data["imageWidth"] = image_width
            self.custom_data["imagePath"] = filename

            # label
            shapes = []
            annotations = json.loads(data[1])
            for annotation in annotations:
                points = annotation["points"]
                shape_type = ShapeType.RECTANGLE.name if is_possible_rectangle(points) else ShapeType.POLYGON.name
                shape = {
                    "label": annotation.get("label", "text"),
                    "description": annotation["transcription"],
                    "points": points,
                    "group_id": annotation.get("id", None),
                    "is_difficult": annotation.get("is_difficult", False),
                    "kie_linking": annotation.get("linking", []),
                    "shape_type": shape_type,
                    "flags": {},
                }
                shapes.append(shape)
            self.custom_data["shapes"] = shapes
            output_file = osp.join(output_path, osp.splitext(filename)[0] + ".json")
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(self.custom_data, f, indent=2, ensure_ascii=False)

    # Export functions
    def custom_to_yolo(self, input_file, output_file, mode, skip_empty_files=False):
        is_empty_file = True
        if osp.exists(input_file):
            with open(input_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            if not skip_empty_files:
                pathlib.Path(output_file).touch()
            return is_empty_file

        image_width = data["imageWidth"]
        image_height = data["imageHeight"]
        image_size = np.array([[image_width, image_height]])
        if mode == "pose":
            pose_data = {}
        with open(output_file, "w", encoding="utf-8") as f:
            for shape in data["shapes"]:
                shape_type = shape["shape_type"]
                if mode == "hbb" and shape_type == "rectangle":
                    label = shape["label"]
                    points = shape["points"]

                    class_index = self.classes.index(label)

                    x_center = (points[0][0] + points[2][0]) / (2 * image_width)
                    y_center = (points[0][1] + points[2][1]) / (2 * image_height)
                    width = abs(points[2][0] - points[0][0]) / image_width
                    height = abs(points[2][1] - points[0][1]) / image_height

                    f.write(f"{class_index} {x_center} {y_center} {width} {height}\n")
                    is_empty_file = False
                elif mode == "seg" and shape_type == ShapeType.POLYGON.name:
                    label = shape["label"]
                    points = np.array(shape["points"])
                    if len(points) < 3:
                        continue
                    class_index = self.classes.index(label)
                    norm_points = points / image_size
                    f.write(f"{class_index} " + " ".join([" ".join([str(cell[0]), str(cell[1])]) for cell in norm_points.tolist()]) + "\n")
                    is_empty_file = False
                elif mode == "obb" and shape_type == ShapeType.ROTATION.name:
                    label = shape["label"]
                    points = shape["points"]
                    if not any(0 <= p[0] < image_width and 0 <= p[1] < image_height for p in points):
                        logger.warning(f"{data['imagePath']}: Skip out of bounds coordinates of {points}!")
                        continue
                    points = list(chain.from_iterable(points))
                    normalized_coords = [
                        points[i] / image_width
                        if i % 2 == 0
                        else points[i] / image_height
                        for i in range(8)
                    ]
                    x0, y0, x1, y1, x2, y2, x3, y3 = normalized_coords
                    class_index = self.classes.index(label)
                    f.write(f"{class_index} {x0} {y0} {x1} {y1} {x2} {y2} {x3} {y3}\n")
                    is_empty_file = False
                elif mode == "pose":
                    if shape_type not in ["rectangle", "point"]:
                        continue
                    label = shape["label"]
                    points = shape["points"]
                    group_id = int(shape["group_id"])
                    if group_id not in pose_data:
                        pose_data[group_id] = {
                            "rectangle": [],
                            "keypoints": {},
                        }
                    if shape_type == ShapeType.RECTANGLE.name:
                        pose_data[group_id]["rectangle"] = points
                        pose_data[group_id]["box_label"] = label
                    else:
                        x, y = points[0]
                        difficult = shape.get("is_difficult", False)
                        visible = 1 if difficult is True else 2
                        pose_data[group_id]["keypoints"][label] = [x, y, visible]
                    is_empty_file = False
            if mode == "pose":
                classes = list(self.pose_classes.keys())
                max_key_points = max([len(kpts) for kpts in self.pose_classes.values()])
                for data in pose_data.values():
                    box_label = data["box_label"]
                    box_index = classes.index(box_label)
                    kpt_names = self.pose_classes[box_label]
                    rectangle = data["rectangle"]
                    x_center = (rectangle[0][0] + rectangle[2][0]) / (2 * image_width)
                    y_center = (rectangle[0][1] + rectangle[2][1]) / (2 * image_height)
                    width = abs(rectangle[2][0] - rectangle[0][0]) / image_width
                    height = abs(rectangle[2][1] - rectangle[0][1]) / image_height
                    x = round(x_center, 6)
                    y = round(y_center, 6)
                    w = round(width, 6)
                    h = round(height, 6)
                    label = f"{box_index} {x} {y} {w} {h}"
                    key_points = data["keypoints"]
                    for name in kpt_names:
                        # 0: Invisible, 1: Occluded, 2: Visible
                        if name not in key_points:
                            if self.has_visible:
                                label += f" 0 0 0"
                            else:
                                label += f" 0 0"
                        else:
                            x, y, visible = key_points[name]
                            x = round((int(x) / image_width), 6)
                            y = round((int(y) / image_height), 6)
                            if self.has_visible:
                                label += f" {x} {y} {visible}"
                            else:
                                label += f" {x} {y}"
                    # Pad the label with zeros to meet 
                    # the yolov8-pose model’s training data format requirements
                    for _ in range(max_key_points - len(kpt_names)):
                        if self.has_visible:
                            label += f" 0 0 0"
                        else:
                            label += f" 0 0"
                    f.write(f"{label}\n")
        return is_empty_file

    def custom_to_voc(self, image_file, input_file, output_dir, mode, skip_empty_files=False):
        is_emtpy_file = True
        image = cv2.imread(image_file)
        image_height, image_width, image_depth = image.shape
        if osp.exists(input_file):
            with open(input_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            shapes = data["shapes"]
        else:
            if not skip_empty_files:
                shapes = []
            else:
                return is_emtpy_file

        image_path = osp.basename(image_file)
        root = Element("annotation")
        SubElement(root, "folder").text = osp.dirname(output_dir)
        ET.SubElement(root, "filename").text = osp.basename(image_path)
        size = ET.SubElement(root, "size")
        ET.SubElement(size, "width").text = str(image_width)
        ET.SubElement(size, "height").text = str(image_height)
        ET.SubElement(size, "depth").text = str(image_depth)
        source = ET.SubElement(root, "source")
        ET.SubElement(source, "database").text = "https://github.com/CVHub520/X-AnyLabeling"
        for shape in shapes:
            label = shape["label"]
            points = shape["points"]
            difficult = shape.get("difficult", False)
            object_elem = ET.SubElement(root, "object")
            ET.SubElement(object_elem, "name").text = label
            ET.SubElement(object_elem, "pose").text = "Unspecified"
            ET.SubElement(object_elem, "truncated").text = "0"
            ET.SubElement(object_elem, "occluded").text = "0"
            ET.SubElement(object_elem, "difficult").text = str(int(difficult))
            if shape["shape_type"] == "rectangle" and mode in ["rectangle", "polygon"]:
                is_emtpy_file = False
                x_min, y_min, x_max, y_max = self.calculate_bounding_box(points)
                bndbox = ET.SubElement(object_elem, "bndbox")
                ET.SubElement(bndbox, "x_min").text = str(int(x_min))
                ET.SubElement(bndbox, "y_min").text = str(int(y_min))
                ET.SubElement(bndbox, "x_max").text = str(int(x_max))
                ET.SubElement(bndbox, "y_max").text = str(int(y_max))
            elif shape["shape_type"] == "polygon" and mode == "polygon":
                if len(points) < 3:
                    continue
                is_emtpy_file = False
                x_min, y_min, x_max, y_max = self.calculate_bounding_box(points)
                bndbox = ET.SubElement(object_elem, "bndbox")
                ET.SubElement(bndbox, "x_min").text = str(int(x_min))
                ET.SubElement(bndbox, "y_min").text = str(int(y_min))
                ET.SubElement(bndbox, "x_max").text = str(int(x_max))
                ET.SubElement(bndbox, "y_max").text = str(int(y_max))
                polygon = ET.SubElement(object_elem, "polygon")
                for i, point in enumerate(points):
                    x_tag = ET.SubElement(polygon, f"x{i + 1}")
                    y_tag = ET.SubElement(polygon, f"y{i + 1}")
                    x_tag.text = str(point[0])
                    y_tag.text = str(point[1])

        xml_string = ET.tostring(root, encoding="utf-8")
        dom = minidom.parseString(xml_string)
        formatted_xml = dom.toprettyxml(indent="  ")

        with open(output_dir, "w", encoding="utf-8") as f:
            f.write(formatted_xml)

        return is_emtpy_file

    def custom_to_coco(self, input_path, output_path, mode):
        coco_data = self.get_coco_data()

        for i, class_name in enumerate(self.classes):
            coco_data["categories"].append(
                {"id": i + 1, "name": class_name, "supercategory": ""}
            )

        image_id = 0
        annotation_id = 0

        label_file_list = os.listdir(input_path)
        for file_name in label_file_list:
            if not file_name.endswith(".json"):
                continue
            image_id += 1
            input_file = osp.join(input_path, file_name)
            with open(input_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            coco_data["images"].append(
                {
                    "id": image_id,
                    "file_name": data["imagePath"],
                    "width": data["imageWidth"],
                    "height": data["imageHeight"],
                    "license": 0,
                    "flickr_url": "",
                    "coco_url": "",
                    "date_captured": "",
                }
            )

            for shape in data["shapes"]:
                annotation_id += 1
                label = shape["label"]
                points = shape["points"]
                difficult = shape.get("difficult", False)
                class_id = self.classes.index(label)
                bbox, segmentation, area = [], [], 0
                shape_type = shape["shape_type"]
                if shape_type == "rectangle" and mode in ["rectangle", "polygon"]:
                    x_min = min(points[0][0], points[2][0])
                    y_min = min(points[0][1], points[2][1])
                    x_max = max(points[0][0], points[2][0])
                    y_max = max(points[0][1], points[2][1])
                    width = x_max - x_min
                    height = y_max - y_min
                    bbox = [x_min, y_min, width, height]
                    area = width * height
                elif shape_type == "polygon" and mode == "polygon":
                    for point in points:
                        segmentation += point
                    bbox = self.get_min_enclosing_bbox(segmentation)
                    area = self.calculate_polygon_area(segmentation)
                    segmentation = [segmentation]

                annotation = {
                    "id": annotation_id,
                    "image_id": image_id,
                    "category_id": class_id + 1,
                    "bbox": bbox,
                    "area": area,
                    "iscrowd": 0,
                    "ignore": int(difficult),
                    "segmentation": segmentation,
                }

                coco_data["annotations"].append(annotation)

        output_file = osp.join(output_path, "instances_default.json")
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(coco_data, f, indent=4, ensure_ascii=False)

    def custom_to_dota(self, input_file, output_file):
        with open(input_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        w, h = data["imageWidth"], data["imageHeight"]
        with open(output_file, "w", encoding="utf-8") as f:
            for shape in data["shapes"]:
                points = shape["points"]
                shape_type = shape["shape_type"]
                if (shape_type != "rotation" or len(points) != 4):
                    continue
                if not any(0 <= p[0] < w and 0 <= p[1] < h for p in points):
                    print(f"{data['imagePath']}: Skip out of bounds coordinates of {points}!")
                    continue
                label = shape["label"]
                difficult = shape.get("difficult", False)
                x0 = points[0][0]
                y0 = points[0][1]
                x1 = points[1][0]
                y1 = points[1][1]
                x2 = points[2][0]
                y2 = points[2][1]
                x3 = points[3][0]
                y3 = points[3][1]
                f.write(
                    f"{x0} {y0} {x1} {y1} {x2} {y2} {x3} {y3} {label} {int(difficult)}\n"
                )

    def custom_to_mask(self, input_file, output_file, mapping_table):
        with open(input_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        image_width = data["imageWidth"]
        image_height = data["imageHeight"]
        image_shape = (image_height, image_width)

        polygons = []
        for shape in data["shapes"]:
            shape_type = shape["shape_type"]
            if shape_type != "polygon":
                continue
            points = shape["points"]
            polygon = []
            for point in points:
                x, y = point
                polygon.append((int(x), int(y)))
            polygons.append(
                {
                    "label": shape["label"],
                    "polygon": polygon,
                }
            )

        output_format = mapping_table["type"]
        if output_format not in ["grayscale", "rgb"]:
            raise ValueError("Invalid output format specified")
        mapping_color = mapping_table["colors"]
        if output_format == "grayscale" and polygons:
            # Initialize binary_mask
            binary_mask = np.zeros(image_shape, dtype=np.uint8)
            for item in polygons:
                label, polygon = item["label"], item["polygon"]
                mask = np.zeros(image_shape, dtype=np.uint8)
                cv2.fillPoly(mask, [np.array(polygon, dtype=np.int32)], 1)
                if label in mapping_color:
                    mask_mapped = mask * mapping_color[label]
                else:
                    mask_mapped = mask
                binary_mask += mask_mapped
            cv2.imencode(".png", binary_mask)[1].tofile(output_file)
        elif output_format == "rgb" and polygons:
            # Initialize rgb_mask
            color_mask = np.zeros(
                (image_height, image_width, 3), dtype=np.uint8
            )
            for item in polygons:
                label, polygon = item["label"], item["polygon"]
                # Create a mask for each polygon
                mask = np.zeros(image_shape[:2], dtype=np.uint8)
                cv2.fillPoly(mask, [np.array(polygon, dtype=np.int32)], 1)
                # Initialize mask_mapped with a default value
                mask_mapped = mask
                # Map the mask values using the provided mapping table
                if label in mapping_color:
                    color = mapping_color[label]
                    mask_mapped = np.zeros_like(color_mask)
                    cv2.fillPoly(
                        mask_mapped, [np.array(polygon, dtype=np.int32)], color
                    )
                    color_mask = cv2.addWeighted(
                        color_mask, 1, mask_mapped, 1, 0
                    )
            cv2.imencode(".png", cv2.cvtColor(color_mask, cv2.COLOR_BGR2RGB))[
                1
            ].tofile(output_file)

    def custom_to_mot(self, input_path, save_path):
        mot_structure = {
            "sequence": dict(
                name="MOT",
                imDir=osp.basename(save_path),
                frameRate=30,
                seqLength=None,
                imWidth=None,
                imHeight=None,
                imExt=None,
            ),
            "det": [],
            "gt": [],
        }
        seg_len, im_widht, im_height, im_ext = 0, None, None, None

        label_file_list = os.listdir(input_path)
        label_file_list.sort(
            key=lambda x: int(osp.splitext(x.rsplit("-", 1)[-1])[0])
            if osp.splitext(x.rsplit("-", 1)[-1])[0].isdigit()
            else 0
        )

        for label_file_name in label_file_list:
            if not label_file_name.endswith("json"):
                continue
            label_file = os.path.join(input_path, label_file_name)
            with open(label_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            seg_len += 1
            if im_widht is None:
                im_widht = data["imageWidth"]
            if im_height is None:
                im_height = data["imageHeight"]
            if im_ext is None:
                im_ext = osp.splitext(osp.basename(data["imagePath"]))[-1]
            frame_id = int(osp.splitext(label_file_name.split("-")[-1])[0])
            for shape in data["shapes"]:
                if shape["shape_type"] != "rectangle":
                    continue
                diccicult = shape.get("diccicult", False)
                class_id = int(self.classes.index(shape["label"]))
                track_id = int(shape["group_id"]) if shape["group_id"] else -1
                points = shape["points"]
                if len(points) == 2:
                    logger.warning(
                        "UserWarning: Diagonal vertex mode is deprecated in X-AnyLabeling release v2.2.0 or later.\n"
                        "Please update your code to accommodate the new four-point mode."
                    )
                    points = rectangle_from_diagonal(points)
                x_min = int(points[0][0])
                y_min = int(points[0][1])
                x_max = int(points[2][0])
                y_max = int(points[2][1])
                boxw = x_max - x_min
                boxh = y_max - y_min
                det = [frame_id, -1, x_min, y_min, boxw, boxh, 1, -1, -1, -1]
                gt = [frame_id, track_id, x_min, y_min, boxw, boxh, int(not diccicult), class_id, 1]
                mot_structure["det"].append(det)
                mot_structure["gt"].append(gt)

        # Save seqinfo.ini
        mot_structure["sequence"]["seqLength"] = seg_len
        mot_structure["sequence"]["imWidth"] = im_widht
        mot_structure["sequence"]["imHeight"] = im_height
        mot_structure["sequence"]["imExt"] = im_ext
        config = configparser.ConfigParser()
        config.add_section('Sequence')
        for key, value in mot_structure["sequence"].items():
            config['Sequence'][key] = str(value)
        with open(osp.join(save_path, "seqinfo.ini"), 'w') as f:
            config.write(f)
        # Save det.txt
        with open(osp.join(save_path, "det.txt"), "w", encoding="utf-8") as f:
            for row in mot_structure["det"]:
                f.write(",".join(map(str, row)) + "\n")
        # Save gt.txt
        with open(osp.join(save_path, "gt.txt"), "w", encoding="utf-8") as f:
            for row in mot_structure["gt"]:
                f.write(",".join(map(str, row)) + "\n")

    def custom_to_odvg(self, image_list, label_path, save_path):
        # Save label_map.json
        label_map = {}
        for i, c in enumerate(self.classes):
            label_map[i] = c
        label_map_file = osp.join(save_path, "label_map.json")
        with open(label_map_file, 'w') as f:
            json.dump(label_map, f)
        # Save od.json
        od_data = []
        for image_file in image_list:
            image_name = osp.basename(image_file)
            label_name = osp.splitext(image_name)[0] + ".json"
            label_file = osp.join(label_path, label_name)
            img = cv2.imdecode(np.fromfile(image_file, dtype=np.uint8), 1)
            height, width = img.shape[:2]
            with open(label_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            instance = []
            for shape in data["shapes"]:
                if (shape["shape_type"] != "rectangle"
                        or shape["label"] not in self.classes):
                    continue
                points = shape["points"]
                x_min = float(points[0][0])
                y_min = float(points[0][1])
                x_max = float(points[2][0])
                y_max = float(points[2][1])
                bbox = [x_min, y_min, x_max, y_max]
                label = self.classes.index(shape["label"])
                category = shape["label"]
                instance.append({
                    "bbox": bbox,
                    "label": label,
                    "category": category
                })
            od_data.append({
                "filename": image_name,
                "height": height,
                "width": width,
                "detection": {
                    "instance": instance
                }
            })
        od_file = osp.join(save_path, "od.json")
        with jsonlines.open(od_file, mode='w') as writer:
            writer.write_all(od_data)

    def custom_to_pporc(self, image_file, label_file, save_path, mode):
        if not osp.exists(label_file):
            return
        image_name = osp.basename(image_file)
        prefix = osp.splitext(image_name)[0]
        dir_name = osp.basename(osp.dirname(image_file))

        avaliable_shape_types = ["rectangle", "rotation", "polygon"]
        img = cv2.imdecode(np.fromfile(image_file, dtype=np.uint8), 1)
        with open(label_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        if mode == "rec":
            crop_img_count, rec_gt, annotations = 0, [], []
            Label_file = osp.join(save_path, "Label.txt")
            rec_gt_file = osp.join(save_path, "rec_gt.txt")
            save_crop_img_path = osp.join(save_path, "crop_img")

            for shape in data["shapes"]:
                shape_type = shape["shape_type"]
                if shape_type not in avaliable_shape_types:
                    continue
                transcription = shape["description"]
                difficult = shape.get("difficult", False)
                points = [list(map(int, p)) for p in shape["points"]]
                annotations.append(dict(
                    transcription=transcription,
                    points=points,
                    difficult=difficult,
                ))
                if len(points) > 4:
                    points = self.gen_quad_from_poly(np.array(points))
                assert len(points) == 4
                img_crop = self.get_rotate_crop_image(img, np.array(points, np.float32))
                if img_crop is None:
                    print(f"Can not recognise the detection box in {image_file}. Please change manually")
                    continue
                crop_img_filenmame = f"{prefix}_crop_{crop_img_count}.jpg"
                crop_img_file = osp.join(save_crop_img_path, crop_img_filenmame)
                cv2.imwrite(crop_img_file, img_crop)
                rec_gt.append(f"crop_img/{crop_img_filenmame}\t{transcription}\n")
                crop_img_count += 1
            if annotations:
                Label = f"{dir_name}/{image_name}\t{json.dumps(annotations, ensure_ascii=False)}\n"
                with open(Label_file, "a", encoding="utf-8") as f:
                    f.write(Label)
                with open(rec_gt_file, "a", encoding="utf-8") as f:
                    for item in rec_gt:
                        f.write(item)
        elif mode == "kie":
            annotations, class_set = [], set()
            ppocr_kie_file = osp.join(save_path, "ppocr_kie.json")
            for shape in data["shapes"]:
                shape_type = shape["shape_type"]
                if shape_type not in avaliable_shape_types:
                    continue
                label = shape["label"]
                class_set.add(label)
                transcription = shape["description"]
                group_id = shape.get("group_id", 0)
                kie_linking = shape.get("kie_linking", [])
                difficult = shape.get("difficult", False)
                points = [list(map(int, p)) for p in shape["points"]]
                annotations.append(dict(
                    transcription=transcription,
                    label=label,
                    points=points,
                    difficult=difficult,
                    id=group_id,
                    linking=kie_linking,
                ))
            if annotations:
                item = f"{dir_name}/{image_name}\t{json.dumps(annotations, ensure_ascii=False)}\n"
                with open(ppocr_kie_file, "a", encoding="utf-8") as f:
                    f.write(item)
            return class_set
