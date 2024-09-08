from typing import List

from PyQt5.QtGui import QImage
from PyQt5.QtWidgets import QMainWindow, QStatusBar, QLineEdit, QListWidget, QPlainTextEdit, QWidget

from core.configs.settings import Settings
from core.dto.label_file import LabelFile


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
        # 当前文件夹下的图片列表
        image_list: List[str] = []
        # 输出目录
        output_dir: str = None
        # 当前正在标注的文件对象 LabelFile
        label_file: LabelFile = LabelFile()
        # 当前正在处理的QImage对象
        image: QImage = None
        # 每个图片的亮度对比度记录
        brightness_contrast_map: dict[str, tuple[float, float]] = {}
        # flag
        flag = None

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


CORE = Core()
