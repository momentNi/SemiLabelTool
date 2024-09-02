#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：SemiLabelTool 
@File ：QtUtils.py
@Author ：Ni Shunjie
@Date ：2024/09/01 20:19 
"""
import os

from PyQt5 import QtWidgets, QtGui
from PyQt5.QtWidgets import QAction


def new_icon(icon):
    return QtGui.QIcon(os.path.join(f":/images/images/{icon}.png"))


def create_new_action(parent, text, slot=None, shortcut=None, icon=None, tip=None, checkable=False, enabled=True,
                      checked=False, auto_trigger=False) -> QAction:
    action = QtWidgets.QAction(text, parent)
    if icon is not None:
        action.setIconText(text.replace(" ", "\n"))
        action.setIcon(new_icon(icon))
    if shortcut is not None:
        if isinstance(shortcut, (list, tuple)):
            action.setShortcuts(shortcut)
        else:
            action.setShortcut(shortcut)
    if tip is not None:
        action.setToolTip(tip)
        action.setStatusTip(tip)
    if slot is not None:
        action.triggered.connect(slot)
    if checkable:
        action.setCheckable(True)
    action.setEnabled(enabled)
    action.setChecked(checked)
    if auto_trigger:
        action.triggered.emit(checked)
    return action
