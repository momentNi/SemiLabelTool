import os

from PyQt5 import QtWidgets, QtGui
from PyQt5.QtWidgets import QAction

from core.configs.core import CORE
from core.services.actions import file_actions


def may_continue() -> bool:
    """
    Check whether the current operation can proceed.

    Returns:
        bool: Whether the current operation can proceed
    """
    if not CORE.Variable.is_dirty:
        return True
    answer = QtWidgets.QMessageBox.question(
        CORE.main_window,
        "Save annotations?",
        f'Save annotations to "{CORE.Variable.current_file_full_path!r}" before closing?',
        QtWidgets.QMessageBox.Save | QtWidgets.QMessageBox.Discard | QtWidgets.QMessageBox.Cancel,
        QtWidgets.QMessageBox.Save,
    )
    if answer == QtWidgets.QMessageBox.Save:
        file_actions.save_file()
        return True
    elif answer == QtWidgets.QMessageBox.Discard:
        return True
    else:
        # answer == QtWidgets.QMessageBox.Cancel
        return False


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
