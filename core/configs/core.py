from typing import List, TYPE_CHECKING

from PyQt5 import QtWidgets

from core.configs.settings import Settings
from core.dto.label_file import LabelFile
from utils.logger import logger

if TYPE_CHECKING:
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
        # 是否有修改待保存
        is_dirty: bool = False
        has_selection_slot = True
        # 当前正在处理的文件名
        current_file_full_path: str = None
        # 上一个打开的文件名
        last_open_dir_path: str = None
        # 输出目录
        output_dir: str = None
        # 当前正在标注的文件对象 LabelFile
        label_file: 'LabelFile' = LabelFile()
        # 当前正在处理的QImage对象
        image: 'QImage' = None
        image_flags: dict = {}
        # 每个图片的亮度对比度记录
        brightness_contrast_map: dict[str, tuple[float, float]] = {}
        # 近期打开的文件
        recent_files: List[str] = settings.get("recent_files", [])
        hidden_class_list = []
        attributes: dict = {}
        copied_shapes: List['Shape'] = []
        selected_polygon_stack: List[int] = []

        # 当前文件夹下的图片列表
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
        # 状态栏
        status_bar: QtWidgets.QStatusBar = None
        # 中心滚动区域
        scroll_area: QtWidgets.QScrollArea = None
        # 画布对象
        canvas: 'Canvas' = None
        # 对象描述信息
        item_description: QtWidgets.QPlainTextEdit = None
        # Information区域
        flag_dock: QtWidgets.QDockWidget = None
        label_dock: QtWidgets.QDockWidget = None
        shape_dock: QtWidgets.QDockWidget = None
        file_dock: QtWidgets.QDockWidget = None

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
