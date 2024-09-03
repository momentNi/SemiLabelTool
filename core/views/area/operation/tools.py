#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：SemiLabelTool 
@File ：tools.py
@Author ：Ni Shunjie
@Date ：2024/09/02 16:33 
"""
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QToolBar


class ToolBar(QToolBar):
    def __init__(self, title):
        super().__init__(title)
        layout = self.layout()
        margin = (0, 0, 0, 0)
        layout.setSpacing(0)
        layout.setContentsMargins(*margin)
        self.setContentsMargins(*margin)
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.FramelessWindowHint)
        self.setStyleSheet(
            """
            QToolBar {
                background: #fff;
                padding: 0px;
                border: 0px;
                border-radius: 5px;
                border: 2px solid #aaa;
            }
            """
        )

    def add_action(self, action):
        if isinstance(action, QtWidgets.QWidgetAction):
            return super().addAction(action)
        btn = QtWidgets.QToolButton()
        btn.setDefaultAction(action)
        btn.setToolButtonStyle(self.toolButtonStyle())
        self.addWidget(btn)

        for i in range(self.layout().count()):
            if isinstance(self.layout().itemAt(i).widget(), QtWidgets.QToolButton):
                self.layout().itemAt(i).setAlignment(QtCore.Qt.AlignCenter)

        return True
