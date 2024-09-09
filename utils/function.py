import os

from PyQt5 import QtGui
from natsort import natsort


def walkthrough_images_in_dir(folder_path):
    extensions = [
        f".{fmt.data().decode().lower()}"
        for fmt in QtGui.QImageReader.supportedImageFormats()
    ]

    images = []
    for root, _, files in os.walk(folder_path):
        for file in files:
            if file.lower().endswith(tuple(extensions)):
                relative_path = os.path.join(root, file)
                images.append(relative_path)
    images = natsort.os_sorted(images)
    return images
