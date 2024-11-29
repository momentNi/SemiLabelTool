import functools

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QToolBar

from core.configs.core import CORE
from core.services.actions.canvas import paint_canvas
from core.services.actions.tools import toggle_object_detection, toggle_segmentation, toggle_chat
from core.views.modules.zoom_widget import ZoomWidget
from utils.qt_utils import create_new_action


class ToolBar(QToolBar):
    def __init__(self, title):
        super().__init__(title)
        self.zoom_widget = None
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

    def generate_actions(self):
        self.__add_action(CORE.Action.open_dir)
        self.__add_action(CORE.Action.open_next_image)
        self.__add_action(CORE.Action.open_prev_image)
        self.__add_action(CORE.Action.save_file)
        self.__add_action(CORE.Action.delete_file)
        self.__add_action(None)
        self.__add_action(CORE.Action.create_mode)
        self.__add_action(CORE.Action.create_rectangle_mode)
        self.__add_action(CORE.Action.create_rotation_mode)
        self.__add_action(CORE.Action.create_circle_mode)
        self.__add_action(CORE.Action.create_line_mode)
        self.__add_action(CORE.Action.create_point_mode)
        self.__add_action(CORE.Action.create_line_strip_mode)
        self.__add_action(CORE.Action.edit_object)
        self.__add_action(CORE.Action.delete_polygon)
        self.__add_action(CORE.Action.undo)
        self.__add_action(None)
        self.__add_action(CORE.Object.zoom_widget_action)
        self.__add_action(CORE.Action.fit_width)
        self.__add_action(None)
        # TODO
        self.__init_auto_buttons()
        # self.__add_action(CORE.Action.object_detection_settings)
        # self.__add_action(CORE.Action.segmentation_settings)
        # self.__add_action(CORE.Action.gpt_settings)
        # self.__add_action(CORE.Action.run_all_images)

        for i in range(self.layout().count()):
            if isinstance(self.layout().itemAt(i).widget(), QtWidgets.QToolButton):
                self.layout().itemAt(i).setAlignment(QtCore.Qt.AlignCenter)

    def generate_zoom_widget(self):
        self.zoom_widget = ZoomWidget()
        self.zoom_widget.setWhatsThis("Zoom in or out of the image. Also accessible with Ctrl++, Ctrl+- and Ctrl+Wheel from the canvas.")
        self.zoom_widget.setEnabled(False)
        self.zoom_widget.valueChanged.connect(paint_canvas)

        CORE.Object.zoom_widget_action = QtWidgets.QWidgetAction(self)
        CORE.Object.zoom_widget_action.setDefaultWidget(self.zoom_widget)
        CORE.Object.zoom_widget = self.zoom_widget

    def __add_action(self, action):
        if action is None:
            return super().addSeparator()
        if isinstance(action, QtWidgets.QWidgetAction):
            return super().addAction(action)
        btn = QtWidgets.QToolButton()
        btn.setDefaultAction(action)
        btn.setToolButtonStyle(self.toolButtonStyle())
        self.addWidget(btn)

    def __init_auto_buttons(self):
        od_btn = QtWidgets.QToolButton()
        od_action = self.menu_action(
            "Object Detection Settings",
            toggle_object_detection,
            None,
            "brain",
            "Object Detection Auto Labeling Settings"
        )
        od_btn.setDefaultAction(od_action)
        od_btn.setToolButtonStyle(self.toolButtonStyle())
        od_btn.setEnabled(False)
        CORE.Object.object_detection_button = od_btn
        self.addWidget(od_btn)

        segment_btn = QtWidgets.QToolButton()
        segment_action = self.menu_action(
            "Segmentation Settings",
            toggle_segmentation,
            None,
            "brain",
            "Segmentation Auto Labeling Settings"
        )
        segment_btn.setDefaultAction(segment_action)
        segment_btn.setToolButtonStyle(self.toolButtonStyle())
        segment_btn.setEnabled(False)
        CORE.Object.segmentation_button = segment_btn
        self.addWidget(segment_btn)

        nlp_btn = QtWidgets.QToolButton()
        nlp_action = self.menu_action(
            "NLP Settings",
            toggle_chat,
            None,
            "brain",
            "NLP Auto Labeling Settings"
        )
        nlp_btn.setDefaultAction(nlp_action)
        nlp_btn.setToolButtonStyle(self.toolButtonStyle())
        nlp_btn.setEnabled(False)
        CORE.Object.nlp_button = nlp_btn
        self.addWidget(nlp_btn)
