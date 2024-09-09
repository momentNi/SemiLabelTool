#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：SemiLabelTool 
@File ：__init__.py.py
@Author ：Ni Shunjie
@Date ：2024/09/02 16:23 
"""
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QScrollArea

from core.configs.core import CORE
from core.services.actions.canvas import get_mode
from core.views.modules.canvas import Canvas


class LabelArea(QWidget):
    def __init__(self, parent=None):
        super().__init__()
        self.parent = parent
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.generate_instruction_part()
        self.generate_auto_part()
        self.generate_canvas_part()

        self.setLayout(self.layout)

    def generate_instruction_part(self):
        content = (
            f"<b>{self.tr("Mode:")}</b> {get_mode()} | "
            f"<b>{self.tr("Shortcuts:")}</b>"
            f" {self.tr("Previous")}(<b>A</b>),"
            f" {self.tr("Next")}(<b>D</b>),"
            f" {self.tr("Rectangle")}(<b>R</b>),"
            f" {self.tr("Polygon")}(<b>P</b>),"
            f" {self.tr("Rotation")}(<b>O</b>)"
        )
        instruction_part = QLabel(content)
        instruction_part.setContentsMargins(0, 0, 0, 0)
        self.layout.addWidget(instruction_part)

    def generate_auto_part(self):
        auto_part = QWidget()
        # TODO Auto labeling part, rely on auto labeling module

        # Default tobe hide
        auto_part.hide()
        self.layout.addWidget(auto_part)

    def generate_canvas_part(self):
        scroll_area = QScrollArea()
        CORE.Object.canvas = Canvas(scroll_area)

        scroll_area.setWidget(CORE.Object.canvas)
        scroll_area.setWidgetResizable(True)

        self.layout.addWidget(scroll_area)
