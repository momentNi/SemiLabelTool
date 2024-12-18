from typing import Tuple

import numpy as np

from core.models.dto.base import ModelInfo
from core.models.dto.yolo.base import YOLO
from core.models.utils.base import scale_boxes


class YOLOv10(YOLO):
    def __init__(self, model_info: ModelInfo):
        super().__init__(model_info)

    def post_process(self, predicts) -> Tuple[np.ndarray, str, float]:
        filter_predicts = predicts[0][0][predicts[0][0][:, 4] >= self.conf_threshold]
        filter_predicts[:, -1] = filter_predicts[:, -1].astype(int)
        if self.filter_classes is not None:
            filter_predicts = filter_predicts[np.isin(filter_predicts[:, -1], self.filter_classes)]

        img_shape = (self.img_height, self.img_width)
        for i, pred in enumerate([filter_predicts]):
            pred[:, :4] = scale_boxes(self.input_shape, pred[:, :4], img_shape)

        bbox = pred[:, :4]
        conf = pred[:, 4:5]
        clas = pred[:, 5:6]
        return bbox, clas, conf
