import os

import yaml


class Settings(object):
    def __init__(self, path=None):
        self.data: dict = {}
        self.path: str = os.path.join(os.path.expanduser("~") if path is None else path, '.semi.cfg')
        self.load()
        if not self.data or self.data.get("reset", False):
            self.reset()
            self.load()

    def __setitem__(self, key: str, value) -> None:
        self.set(key, value)

    def __getitem__(self, key: str) -> object:
        return self.get(key)

    def set(self, key: str, value) -> None:
        self.data[key] = value

    def get(self, key, default=None) -> object:
        if key in self.data:
            return self.data[key]
        return default

    def save(self) -> bool:
        if self.path:
            with open(self.path, 'w') as f:
                yaml.safe_dump(self.data, f)
                return True
        return False

    def load(self) -> None:
        """
        加载既有 settings 配置
        Returns:
            bool: 是否加载成功
        """
        if os.path.exists(self.path):
            # noinspection PyBroadException
            try:
                with open(self.path, 'rb') as f:
                    self.data = yaml.safe_load(f)
            except Exception:
                os.remove(self.path)
                with open(os.path.join(os.path.dirname(os.path.relpath(__file__)), "config.yaml"), "rb") as f:
                    self.data = yaml.safe_load(f)
        else:
            with open(os.path.join(os.path.dirname(os.path.relpath(__file__)), "config.yaml"), "rb") as f:
                self.data = yaml.safe_load(f)

    def reset(self):
        if os.path.exists(self.path):
            os.remove(self.path)
        self.data = {}
