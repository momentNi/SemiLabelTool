import os
import pickle

from utils.logger import logger


class Settings(object):
    def __init__(self, path=None):
        self.data: dict = {}
        self.path: str = os.path.join(os.path.expanduser("~") if path is None else path, '.semi.pkl')

    def __setitem__(self, key: str, value):
        self.data[key] = value

    def __getitem__(self, key):
        return self.data[key]

    def get(self, key, default=None):
        if key in self.data:
            return self.data[key]
        return default

    def save(self):
        if self.path:
            with open(self.path, 'wb') as f:
                pickle.dump(self.data, f, pickle.HIGHEST_PROTOCOL)
                return True
        return False

    def load(self):
        try:
            if os.path.exists(self.path):
                with open(self.path, 'rb') as f:
                    self.data = pickle.load(f)
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
