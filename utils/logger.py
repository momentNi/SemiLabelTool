import logging
import string

from core.configs.constants import Constants


class ColorFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord):
        fmt_template = string.Template(f"{Constants.COLORS[record.levelno]}{Constants.FORMAT}\x1b[0m")
        return fmt_template.substitute(record.__dict__)


class SemiLogger(logging.Logger):
    def __init__(self, name):
        super().__init__(name, logging.DEBUG)

        file_handler = logging.FileHandler("../logs/app.log", mode='w')
        file_handler.setFormatter(logging.Formatter(Constants.FORMAT, datefmt='%Y-%m-%d %H:%M:%S', style="$"))
        self.addHandler(file_handler)

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(ColorFormatter())
        self.addHandler(console_handler)


logger = SemiLogger("SemiLabelTool")
