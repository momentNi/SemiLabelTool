import argparse
import os
import sys

from PyQt5 import QtCore
from PyQt5.QtWidgets import QApplication

from core.configs.constants import Constants
from core.configs.core import CORE
from core.resources import resources
from utils.logger import logger
from utils.qt_utils import new_icon
from views.main_window import MainWindow

sys.path.append('.')


def load_parser(parser):
    """
    读取预参数

    :param parser: ArgumentParser
    :return: ArgumentParser
    """
    parser.add_argument(
        "--epsilon",
        type=float,
        help="epsilon to find nearest vertex on canvas",
        default=argparse.SUPPRESS,
    )
    parser.add_argument(
        "image_dir",
        nargs="?"
    )
    parser.add_argument(
        "class_file",
        default=os.path.join(os.path.dirname(__file__), "data", "predefined_classes.txt"),
        nargs="?"
    )
    parser.add_argument(
        "save_dir",
        nargs="?"
    )

    return parser


def main():
    parser = load_parser(argparse.ArgumentParser())
    args = parser.parse_args()

    # Enable scaling for high dpi screens
    QApplication.setAttribute(QtCore.Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
    # enable high dpi scaling
    QApplication.setAttribute(QtCore.Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)
    # use high dpi icons
    QtCore.QCoreApplication.setAttribute(QtCore.Qt.ApplicationAttribute.AA_ShareOpenGLContexts)

    app = QApplication(sys.argv)
    app.processEvents()
    app.setApplicationName(Constants.APP_NAME)
    # Resources package must be imported, but no need to use directly.
    # Print here to simply avoid optimize import.
    logger.debug(resources)
    logger.debug(CORE)
    app.setWindowIcon(new_icon("icon"))
    win = MainWindow(app, config=args)
    win.showMaximized()
    win.raise_()

    sys.exit(app.exec())


if __name__ == '__main__':
    main()
