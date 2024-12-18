from typing import Tuple

import numpy as np

from core.models.dto.base import ModelInfo
from core.models.dto.yolo.yolo_v7 import YOLOv7


class YOLOv5(YOLOv7):
    def __init__(self, model_info: ModelInfo):
        super().__init__(model_info)

    def post_process(self, predicts) -> Tuple[np.ndarray, str, float]:
        if self.anchors:
            outs = predicts[0]
            row_ind = 0
            for i in range(self.nl):
                h = int(self.input_shape[0] / self.stride[i])
                w = int(self.input_shape[1] / self.stride[i])
                length = int(self.na * h * w)
                if self.grid[i].shape[2:4] != (h, w):
                    xv, yv = np.meshgrid(np.arange(h), np.arange(w))
                    self.grid[i] = np.stack((xv, yv), 2).reshape((-1, 2)).astype(np.float32)
                outs[row_ind: row_ind + length, 0:2] = outs[row_ind: row_ind + length, 0:2] * 2.0 - 0.5 + np.tile(self.grid[i], (self.na, 1)) * int(self.stride[i])
                outs[row_ind: row_ind + length, 2:4] = (outs[row_ind: row_ind + length, 2:4] * 2) ** 2 * np.repeat(self.anchor_grid[i], h * w, axis=0)
                row_ind += length
            predicts = outs[np.newaxis, :]
        return super().post_process(predicts)
