from typing import List

from PyQt5.QtGui import QImage
from PyQt5.QtWidgets import QMainWindow, QStatusBar, QLineEdit, QListWidget, QPlainTextEdit, QWidget, QAction

from core.configs.settings import Settings
from core.dto.label_file import LabelFile
from utils.logger import logger


class Core(object):
    """
    记录系统当前全局状态
    """

    class Variable:
        settings = Settings()
        # 是否有修改待保存
        is_dirty: bool = False
        # 当前正在处理的文件名
        current_file_full_path: str = None
        #
        last_open_dir_path: str = None
        # 输出目录
        output_dir: str = None
        # 当前正在标注的文件对象 LabelFile
        label_file: LabelFile = LabelFile()
        # 当前正在处理的QImage对象
        image: QImage = None
        # 每个图片的亮度对比度记录
        brightness_contrast_map: dict[str, tuple[float, float]] = {}
        recent_files: List[str] = settings.get("recent_files", [])

        @classmethod
        @property
        def image_list(self):
            lst = []
            for i in range(CORE.Object.info_file_list.count()):
                item = CORE.Object.info_file_list.item(i)
                lst.append(item.text())
            return lst

    class Object:
        # 主窗口对象
        main_window: QMainWindow = None
        # 状态栏
        status_bar: QStatusBar = None
        # 画布对象
        canvas: QWidget = None
        # 对象描述信息
        item_description: QPlainTextEdit = None
        # Information区域文件列表
        info_file_search: QLineEdit = None
        info_file_list: QListWidget = None
        # ToolBar 缩放组件
        zoom_widget = None

    class Action:
        def __init__(self):
            self.actions = {}

        def __getattr__(self, name) -> QAction | None:
            if name not in self.actions:
                logger.error(f"Action not exists: {name}")
                return None
            return self.actions.get(name)

        def __setattr__(self, name, q_action):
            if name in self.actions:
                logger.warning(f"{name} has already defined in actions")
                return
            elif not isinstance(q_action, QAction):
                logger.error(f"{name} has invalid QAction: {q_action}")
                return
            self.actions[name] = q_action

CORE = Core()
