import base64
import io
import os

import PIL.ExifTags
import PIL.Image
import PIL.ImageOps
import cv2
import numpy as np
import qimage2ndarray
from PyQt5.QtGui import QImage


def img_data_to_pil(img_data):
    f = io.BytesIO()
    f.write(img_data)
    img_pil = PIL.Image.open(f)
    return img_pil


def img_data_to_arr(img_data):
    img_pil = img_data_to_pil(img_data)
    img_arr = np.array(img_pil)
    return img_arr


def img_b64_to_arr(img_b64):
    img_data = base64.b64decode(img_b64)
    img_arr = img_data_to_arr(img_data)
    return img_arr


def img_pil_to_data(img_pil):
    f = io.BytesIO()
    img_pil.save(f, format="PNG")
    img_data = f.getvalue()
    return img_data


def img_arr_to_b64(img_arr):
    img_pil = PIL.Image.fromarray(img_arr)
    f = io.BytesIO()
    img_pil.save(f, format="PNG")
    img_bin = f.getvalue()
    if hasattr(base64, "encodebytes"):
        img_b64 = base64.encodebytes(img_bin)
    else:
        img_b64 = base64.encodestring(img_bin)
    return img_b64


def img_data_to_png_data(img_data):
    with io.BytesIO() as f:
        f.write(img_data)
        img = PIL.Image.open(f)

        with io.BytesIO() as f:
            img.save(f, "PNG")
            f.seek(0)
            return f.read()


def apply_exif_orientation(image):
    try:
        exif = image._getexif()
    except AttributeError:
        exif = None

    if exif is None:
        return image

    exif = {
        PIL.ExifTags.TAGS[k]: v
        for k, v in exif.items()
        if k in PIL.ExifTags.TAGS
    }

    orientation = exif.get("Orientation", None)

    if orientation == 1:
        # do nothing
        return image
    if orientation == 2:
        # left-to-right mirror
        return PIL.ImageOps.mirror(image)
    if orientation == 3:
        # rotate 180
        return image.transpose(PIL.Image.ROTATE_180)
    if orientation == 4:
        # top-to-bottom mirror
        return PIL.ImageOps.flip(image)
    if orientation == 5:
        # top-to-left mirror
        return PIL.ImageOps.mirror(image.transpose(PIL.Image.ROTATE_270))
    if orientation == 6:
        # rotate 270
        return image.transpose(PIL.Image.ROTATE_270)
    if orientation == 7:
        # top-to-right mirror
        return PIL.ImageOps.mirror(image.transpose(PIL.Image.ROTATE_90))
    if orientation == 8:
        # rotate 90
        return image.transpose(PIL.Image.ROTATE_90)
    return image


def qt_img_to_rgb_cv_img(qt_img, img_path=None):
    """
    Convert 8bit/16bit RGB image or 8bit/16bit Gray image to 8bit RGB image
    """
    if img_path is not None and os.path.exists(img_path):
        cv_image = cv2.imdecode(np.fromfile(img_path, dtype=np.uint8), -1)
        cv_image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)
    else:
        if qt_img.format() in (QImage.Format_RGB32, QImage.Format_ARGB32, QImage.Format_ARGB32_Premultiplied):
            cv_image = qimage2ndarray.rgb_view(qt_img)
        else:
            cv_image = qimage2ndarray.raw_view(qt_img)
    # To uint8
    if cv_image.dtype != np.uint8:
        cv2.normalize(cv_image, cv_image, 0, 255, cv2.NORM_MINMAX)
        cv_image = np.array(cv_image, dtype=np.uint8)
    # To RGB
    if len(cv_image.shape) == 2 or cv_image.shape[2] == 1:
        cv_image = cv2.merge([cv_image, cv_image, cv_image])
    return cv_image


def qt_img_to_cv_img(in_image):
    return qimage2ndarray.rgb_view(in_image)


def cv_img_to_qt_img(in_mat):
    return QImage(qimage2ndarray.array2qimage(in_mat))
