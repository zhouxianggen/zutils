import urllib
import base64
from io import BytesIO
from shapely.geometry import Polygon
from PIL import Image
import numpy as np
import cv2


def b642cv2(data):
    arr = np.asarray(bytearray(base64.b64decode(data)), dtype=np.uint8)
    return cv2.imdecode(arr, cv2.IMREAD_COLOR)


def cv22b64(image, ext='.jpg'):
    return base64.b64encode(cv2.imencode(ext, image)[1].tostring()).decode('utf8')


def b642pil(data):
    return Image.open(BytesIO(base64.b64decode(data)))


def pil2b64(image):
    img = cv2.cvtColor(np.asarray(image), cv2.COLOR_RGB2BGR)
    return cv22b64(img)


def pil2cv2(image):
    return cv2.cvtColor(np.asarray(image), cv2.COLOR_RGB2BGR)


def cv22pil(image):
    return Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))


def load_image_cv2(src, src_type):
    if src_type == 'base64':
        return b642cv2(src)
    elif src_type == 'url':
        arr = np.asarray(bytearray(urllib.request.urlopen(src).read()), 
                dtype=np.uint8)
        return cv2.imdecode(arr, cv2.IMREAD_COLOR)


def load_image_pil(src, src_type):
    if src_type == 'base64':
        return b642pil(src)
    elif src_type == 'url':
        return Image.open(BytesIO(urllib.request.urlopen(src).read()))


def load_image(src, src_type):
    return load_image_cv2(src, src_type)


def get_in_area_percentage(obj, area):
    p1 = Polygon(obj)
    p2 = Polygon(area)
    p3 = p1.intersection(p2)
    return p3.area / p1.area


def get_iap(obj, area):
    return get_in_area_percentage(obj, area)


def bbox2polygon(b):
    return [(b[0], b[1]), (b[2], b[1]), (b[2], b[3]), (b[0], b[3])]


def get_iou(b1, b2):
    p1 = Polygon(bbox2polygon(b1))
    p2 = Polygon(bbox2polygon(b2))
    p3 = p1.intersection(p2)
    union = p1.area + p2.area - p3.area
    return (p3.area/union) if union else 0

