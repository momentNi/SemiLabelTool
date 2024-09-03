#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：SemiLabelTool 
@File ：file.py
@Author ：Ni Shunjie
@Date ：2024/09/02 10:49 
"""

from core.services.actions.files import *
from core.views.area.menu.sub import BaseMenu


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
