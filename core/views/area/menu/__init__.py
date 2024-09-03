#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：SemiLabelTool 
@File ：__init__.py
@Author ：Ni Shunjie
@Date ：2024/09/01 16:02 
"""
from PyQt5.QtWidgets import QMenuBar

from core.views.area.menu.sub.file import FileMenu


class LabelMenuBar(QMenuBar):
    def __init__(self, parent=None):
        super(LabelMenuBar, self).__init__()
        self.menu_bar = QMenuBar(parent)
        self.menu_bar.addMenu(FileMenu("文件", self.menu_bar).get_menu())

    def get_menu_bar(self):
        return self.menu_bar
