#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：SemiLabelTool 
@File ：file.py
@Author ：Ni Shunjie
@Date ：2024/09/02 10:49 
"""
import os

from PyQt5 import QtGui

from core.configs.constants import Constants
from core.dto.label_file import LabelFile
from core.views.modules.common.previews import FileDialogPreview
from core.views.modules.menu.sub import BaseMenu


class FileMenu(BaseMenu):

    def __init__(self, name, parent):
        super().__init__(name, parent)

    def add_actions(self):
        self.addAction(self.menu_action(
            self.tr("&Open File"),
            open_file,
            "Ctrl+O",
            "file",
            self.tr("Open image or label file")
        ))


def open_file(self, _value=False):
    if not self.may_continue():
        return
    path = os.path.dirname(str(self.filename)) if self.filename else "."
    formats = [
        f"*.{fmt.data().decode()}"
        for fmt in QtGui.QImageReader.supportedImageFormats()
    ]
    filters = self.tr("Image & Label files (%s)") % " ".join(
        formats + [f"*{LabelFile.suffix}"]
    )
    file_dialog = FileDialogPreview(self)
    file_dialog.setFileMode(FileDialogPreview.ExistingFile)
    file_dialog.setNameFilter(filters)
    file_dialog.setWindowTitle(
        self.tr("%s - Choose Image or Label file") % Constants.APP_NAME,
    )
    file_dialog.setWindowFilePath(path)
    file_dialog.setViewMode(FileDialogPreview.Detail)
    if file_dialog.exec_():
        filename = file_dialog.selectedFiles()[0]
        if filename:
            self.file_list_widget.clear()
            self.load_file(filename)
