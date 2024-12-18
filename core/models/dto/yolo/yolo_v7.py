from typing import Tuple

import numpy as np

from core.models.dto.base import ModelInfo
from core.models.dto.yolo.base import YOLO
from core.models.utils.base import xywh2xyxy, numpy_nms, scale_boxes


class YOLOv7(YOLO):
    def __init__(self, model_info: ModelInfo):
        super().__init__(model_info)

    def post_process(self, predicts) -> Tuple[np.ndarray, str, float]:
        prediction = predicts[0]
        if isinstance(prediction, (list, tuple)):
            # select only inference output
            prediction = prediction[0]

        # batch size
        bs = prediction.shape[0]
        # number of classes
        nc = prediction.shape[2] - 5
        nm = prediction.shape[2] - nc - 5
        # mask start index
        mi = 5 + nc
        # candidates
        xc = prediction[..., 4] > self.conf_threshold

        prediction[..., :4] = xywh2xyxy(prediction[..., :4])
        output = [np.zeros((0, 6 + nm))] * bs

        # image index, image inference
        for xi, x in enumerate(prediction):
            # Apply constraints
            # x[((x[:, 2:4] < min_wh) |
            # (x[:, 2:4] > max_wh)).any(1), 4] = 0  # width-height
            # confidence
            x = x[xc[xi]]

            if not x.shape[0]:
                continue

            # Compute conf = obj_conf * cls_conf
            x[:, 5:] *= x[:, 4:5]

            box = x[:, :4]
            mask = x[:, mi:]
            cls = x[:, 5:mi]

            conf = np.max(cls, axis=1, keepdims=True)
            j = np.argmax(cls, axis=1, keepdims=True)
            x = np.concatenate((box, conf, j.astype(float), mask), axis=1)[conf.flatten() > self.conf_threshold]
            if self.filter_classes is not None:
                x = x[(x[:, 5:6] == np.array(self.filter_classes)).any(1)]

            n = x.shape[0]
            if not n:
                continue
            if n > 30000:
                x = x[np.argsort(x[:, 4])[::-1][:30000]]

            c = x[:, 5:6] * (0 if self.agnostic else 7680)
            boxes, scores = x[:, :4] + c, x[:, 4]
            i = numpy_nms(boxes, scores, self.iou_threshold)
            i = i[:300]

            output[xi] = x[i]

        img_shape = (self.img_height, self.img_width)

        for i, pred in enumerate(output):
            pred[:, :4] = scale_boxes(self.input_shape, pred[:, :4], img_shape)

        bbox = pred[:, :4]
        conf = pred[:, 4:5]
        clas = pred[:, 5:6]

        return bbox, clas, conf
