from PyQt5 import QtCore
from PyQt5.QtGui import QColor

from core.views.modules.common.shape import Shape


class LabelingWidget(LabelDialog):
    """The main widget for labeling images"""

    FIT_WINDOW, FIT_WIDTH, MANUAL_ZOOM = 0, 1, 2
    next_files_changed = QtCore.pyqtSignal(list)

    def __init__(self, parent, config=None):
        super().__init__()
        self.parent = parent
        self.image_path = None
        self.image_data = None
        self.label_file = None
        self.other_data = {}
        self.classes_file = None
        self.attributes = {}
        self.current_category = None
        self.selected_polygon_stack = []
        self.available_shapes = Shape.get_available_shapes()
        self.hidden_cls = []

        # see configs/anylabeling_config.yaml for valid configuration
        if config is None:
            config = get_config()
        self._config = config

        # set default shape colors
        Shape.line_color = QColor(*self._config["shape"]["line_color"])
        Shape.fill_color = QColor(*self._config["shape"]["fill_color"])
        Shape.select_line_color = QColor(
            *self._config["shape"]["select_line_color"]
        )
        Shape.select_fill_color = QColor(
            *self._config["shape"]["select_fill_color"]
        )
        Shape.vertex_fill_color = QColor(
            *self._config["shape"]["vertex_fill_color"]
        )
        Shape.hvertex_fill_color = QColor(
            *self._config["shape"]["hvertex_fill_color"]
        )

        # Set point size from config file
        Shape.point_size = self._config["shape"]["point_size"]

        super(LabelDialog, self).__init__()
