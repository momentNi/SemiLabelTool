import hashlib
import os
import re
import socket
import struct
from difflib import SequenceMatcher
from typing import Tuple

from PyQt5 import QtGui
from natsort import natsort

from core.configs.core import CORE


def has_chinese(s):
    return bool(re.search('[\u4e00-\u9fff]', str(s)))


def walkthrough_files_in_dir(folder_path):
    extensions = [
        f".{fmt.data().decode().lower()}"
        for fmt in QtGui.QImageReader.supportedImageFormats()
    ]

    file_list = []
    for root, _, files in os.walk(folder_path):
        for file in files:
            if file.lower().endswith(tuple(extensions)):
                relative_path = os.path.join(root, file)
                file_list.append(relative_path)
    file_list = natsort.os_sorted(file_list)
    return file_list


def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))


def get_rgb_by_label(label: str) -> Tuple[int, int, int]:
    if label in CORE.Variable.label_info:
        return CORE.Variable.label_info[label]["color"]
    m = hashlib.blake2s()
    m.update(label.encode('utf-8'))
    hash_result = m.hexdigest()
    # take first 3 bytes
    hash_bytes = hash_result[:6]
    # convert to int(4 bytes) and take first 3 bytes as R, G, B
    num = int(hash_bytes, 16)

    r, g, b, _ = struct.unpack('BBBB', struct.pack('I', num))

    return r, g, b


def find_most_similar_label(text, valid_labels):
    max_similarity = 0
    most_similar_label = valid_labels[0]
    for label in valid_labels:
        similarity = SequenceMatcher(None, text, label).ratio()
        if similarity > max_similarity:
            max_similarity = similarity
            most_similar_label = label
    return most_similar_label


def is_possible_rectangle(points):
    if len(points) != 4:
        return False

    # Check if four points form a rectangle
    # The points are expected to be in the format:
    # [[x1, y1], [x2, y2], [x3, y3], [x4, y4]]
    dists = [square_distance(points[i], points[(i + 1) % 4]) for i in range(4)]
    dists.sort()

    # For a rectangle, the two smallest distances
    # should be equal and the two largest should be equal
    return dists[0] == dists[1] and dists[2] == dists[3]


def square_distance(p, q):
    # Calculate the square distance between two points
    return (p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2


def is_address_reachable(ip, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((ip, int(port)))
        s.shutdown(2)
        return True
    except Exception:
        return False
