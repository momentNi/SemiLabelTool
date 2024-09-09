import os
import re

from PyQt5 import QtGui
from natsort import natsort


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
