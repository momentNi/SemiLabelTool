#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：SemiLabelTool 
@File ：__init__.py.py
@Author ：Ni Shunjie
@Date ：2024/09/02 16:23 
"""
from PyQt5.QtWidgets import QWidget


class InformationArea(QWidget):
    def __init__(self, parent=None):
        super().__init__()
        self.parent = parent
