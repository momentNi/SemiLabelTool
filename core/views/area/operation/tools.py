import functools

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QToolBar

from core.configs.core import CORE
from core.views.modules.zoom_widget import ZoomWidget
from utils.qt_utils import create_new_action


class ToolBar(QToolBar):
    def __init__(self, title):
        super().__init__(title)
        self.menu_action = functools.partial(create_new_action, self)
        self.setContentsMargins(0, 0, 0, 0)
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
        layout = self.layout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        self.__init_zoom_widget()

        self.add_action(CORE.Action.open_dir)
        self.add_action(CORE.Action.open_next_image)
        self.add_action(CORE.Action.open_prev_image)
        self.add_action(CORE.Action.save_file)
        self.add_action(CORE.Action.delete_file)
        self.add_action(None)
        self.add_action(CORE.Action.create_mode)
        self.add_action(CORE.Action.create_rectangle_mode)
        self.add_action(CORE.Action.create_rotation_mode)
        self.add_action(CORE.Action.create_circle_mode)
        self.add_action(CORE.Action.create_line_mode)
        self.add_action(CORE.Action.create_point_mode)
        self.add_action(CORE.Action.create_line_strip_mode)
        self.add_action(CORE.Action.edit_object)
        self.add_action(CORE.Action.delete_polygon)
        self.add_action(CORE.Action.undo)
        self.add_action(None)
        self.add_action(CORE.Object.zoom_widget_action)
        # TODO
        # fit_width, toggle_auto_labeling_widget, run_all_images,

    def add_action(self, action):
        if action is None:
            return super().addSeparator()
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

    def __init_zoom_widget(self):

        self.zoom_widget = ZoomWidget()
        self.zoom_widget.setWhatsThis(
            "Zoom in or out of the image. Also accessible with Ctrl++, Ctrl+- and Ctrl+Wheel from the canvas.")
        self.zoom_widget.setEnabled(False)
        # TODO
        self.zoom_widget.valueChanged.connect(self.paint_canvas)

        CORE.Object.zoom_widget_action = QtWidgets.QWidgetAction(self)
        CORE.Object.zoom_widget_action.setDefaultWidget(self.zoom_widget)
        CORE.Object.zoom_widget = self.zoom_widget

    def paint_canvas(self):
        print(self.zoom_widget.value())
