import os

import yaml

from utils.logger import logger


class Settings(object):
    def __init__(self, path=None):
        self.data: dict = {}
        self.path: str = os.path.join(os.path.expanduser("~") if path is None else path, '.semi.cfg')

    def __setitem__(self, key: str, value) -> None:
        self.data[key] = value

    def __getitem__(self, key: str) -> object:
        return self.data[key]

    def get(self, key, default=None) -> object:
        if key in self.data:
            return self.data[key]
        return default

    def save(self) -> bool:
        if self.path:
            with open(self.path, 'wb') as f:
                yaml.safe_dump(self.data, f)
                return True
        return False

    def load(self) -> bool:
        """
        加载既有 settings 配置
        Returns:
            bool: 是否加载成功
        """
        try:
            if os.path.exists(self.path):
                with open(self.path, 'rb') as f:
                    self.data = yaml.safe_load(f)
                    return True
        except IOError:
            logger.error('Loading setting failed')
        return False

    def reset(self):
        if os.path.exists(self.path):
            os.remove(self.path)
            logger.info('Remove settings file ${0}'.format(self.path))
        self.data = {}
        self.path = None


settings = Settings()
