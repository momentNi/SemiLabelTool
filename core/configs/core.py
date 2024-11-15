from typing import List, TYPE_CHECKING, Optional

from PyQt5 import QtWidgets

from core.configs.settings import Settings
from utils.logger import logger

if TYPE_CHECKING:
    from core.dto.label_file import LabelFile
    from PyQt5.QtGui import QImage
    from core.dto.shape import Shape
    from core.views.dialogs.label_dialog import LabelDialog
    from core.views.modules.canvas import Canvas
    from core.views.modules.label_list_widget import LabelListWidget
    from core.views.modules.label_filter_combo_box import LabelFilterComboBox
    from core.views.modules.unique_label_list_widget import UniqueLabelListWidget
    from core.views.modules.zoom_widget import ZoomWidget


class Core(object):
    """
    记录系统当前全局状态
    """

    class Variable:
        settings: 'Settings' = Settings()
        is_dirty: bool = False
        has_selection_slot = True
        current_file_full_path: str = None
        last_open_dir_path: str = None
        output_dir: str = None
        label_file: Optional['LabelFile'] = None
        image: 'QImage' = None
        image_path: str = None
        image_data: str = None
        image_flags: dict = {}
        other_data: dict = {}
        label_info: dict = {}
        brightness_contrast_map: dict[str, tuple[float, float]] = {}
        recent_files: List[str] = settings.get("recent_files", [])
        hidden_class_list = []
        attributes: dict = {}
        copied_shapes: List['Shape'] = []
        selected_polygon_stack: List[int] = []
        shape_scale: float = 1.5

        @classmethod
        @property
        def image_list(self):
            lst = []
            for i in range(CORE.Object.info_file_list_widget.count()):
                item = CORE.Object.info_file_list_widget.item(i)
                lst.append(item.text())
            return lst

    class Object:
        # 主窗口对象
        main_window: QtWidgets.QMainWindow = None
        instruction_part: QtWidgets.QLabel = None
        # 状态栏
        status_bar: QtWidgets.QStatusBar = None
        # 中心滚动区域
        scroll_area: QtWidgets.QScrollArea = None
        # 画布对象
        canvas: 'Canvas' = None
        # 对象描述信息
        item_description: QtWidgets.QPlainTextEdit = None
        # Information区域
        tab_widget: QtWidgets.QTabWidget = None
        file_tab_widget: QtWidgets.QWidget = None
        label_tab_widget: QtWidgets.QWidget = None
        image_tab_widget: QtWidgets.QWidget = None

        attribute_content_area: QtWidgets.QScrollArea = None
        flag_widget: QtWidgets.QListWidget = None
        # 文件列表
        info_file_search_widget: QtWidgets.QLineEdit = None
        info_file_list_widget: QtWidgets.QListWidget = None

        label_list_widget: 'LabelListWidget' = None
        label_filter_combo_box: 'LabelFilterComboBox' = None
        unique_label_list_widget: 'UniqueLabelListWidget' = None

        label_dialog: 'LabelDialog' = None

        # ToolBar 缩放组件
        zoom_widget: 'ZoomWidget' = None

    class Action:
        def __init__(self):
            self.actions = {}

        def __getattr__(self, name) -> QtWidgets.QAction | None:
            if name not in self.actions:
                logger.error(f"Action not exists: {name}")
                return None
            return self.actions.get(name)

        def __setattr__(self, name, q_action):
            if name in self.actions:
                logger.warning(f"{name} has already defined in actions")
                return
            elif not isinstance(q_action, QtWidgets.QAction):
                logger.error(f"{name} has invalid QAction: {q_action}")
                return
            self.actions[name] = q_action


CORE = Core()
