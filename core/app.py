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


def main():
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
    win = MainWindow(app)
    win.resize(*CORE.Variable.settings.get("window/size", (600, 500)))
    win.move(*CORE.Variable.settings.get("window/position", (0, 0)))
    win.show()
    win.raise_()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
