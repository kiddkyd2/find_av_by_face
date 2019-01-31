import cv2
import base64
import numpy as np


def base64photo(img_path):
    with open(img_path, "rb") as f:
        base64_data = base64.b64encode(f.read())
        return bytes.decode(base64_data)


img = open('./source_img/angelababy.jpg', 'rb')
img_b = base64.b64encode(img.read())
print(img_b)
imD = base64.b64decode(img_b)
nparr = np.fromstring(imD, np.uint8)
# cv2.IMREAD_COLOR 以彩色模式读入 1
# cv2.IMREAD_GRAYSCALE 以灰色模式读入 0
image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
cv2.imshow('Image', image)
cv2.waitKey()
