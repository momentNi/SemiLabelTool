from typing import Tuple

import numpy as np

from core.models.dto.yolo import YOLO
from core.models.utils.base import scale_boxes, numpy_nms, xywh2xyxy


class YOLOv9(YOLO):
    def __init__(self, name, label, platform, model_type, config_path):
        super().__init__(name, label, platform, model_type, config_path)

    def post_process(self, predicts) -> Tuple[np.ndarray, str, float]:
        if isinstance(predicts[0], (list, tuple)):
            # select only inference output
            predicts[0] = predicts[0][0]
        # batch size
        bs = predicts[0].shape[0]
        # number of classes
        nc = predicts[0].shape[1] - 4
        nm = predicts[0].shape[1] - nc - 4
        # mask start index
        mi = 4 + nc
        # candidates
        xc = np.amax(predicts[0][:, 4:mi], axis=1) > self.conf_threshold

        # shape(1,84,6300) to shape(1,6300,84)
        prediction = np.transpose(predicts[0], (0, 2, 1))
        prediction[..., :4] = xywh2xyxy(prediction[..., :4])
        output = [np.zeros((0, 6 + nm))] * bs

        # image index, image inference
        for xi, x in enumerate(prediction):
            # Apply constraints
            # x[((x[:, 2:4] < min_wh) | (x[:, 2:4] > max_wh)).any(1), 4] = 0  # width-height
            # confidence
            x = x[xc[xi]]

            if not x.shape[0]:
                continue

            box = x[:, :4]
            cls = x[:, 4: 4 + nc]
            mask = x[:, 4 + nc: 4 + nc + nm]

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
            scores = x[:, 4]
            boxes = x[:, :4] + c
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

    def unload(self):
        del self.net
