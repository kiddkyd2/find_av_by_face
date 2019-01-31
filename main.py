import base64
import configparser
import json
import os
import sqlite3
import time

from my_baidu.tsbaidu import FaceBaiDu
from my_dlib.tsdlib import FaceDlib


def get_config(section, key):
    config = configparser.ConfigParser()
    path = os.getcwd() + '/config.conf'
    config.read(path)
    return config.get(section, key)


def base64photo(img_path):
    with open(img_path, "rb") as f:
        base64_data = base64.b64encode(f.read())
        return bytes.decode(base64_data)


conn = sqlite3.connect(get_config('db', 'path'))
cur = conn.cursor()

g_source_img = './source_img/angelababy.jpg'
g_source_img_info = {}
g_img_list = []
g_result_list = []


def init():
    global g_source_img_info
    g_source_img_info = {'imgurl': g_source_img, 'username': g_source_img.split('/')[-1].split('.')[0],
                         'videourl': '', 'buf': base64photo(g_source_img)}


def load_img():
    try:
        rows = cur.execute("select * from face_youma limit 2")
        for row in rows:
            g_img_list.append({'imgurl': row[0], 'username': row[1], 'videourl': row[2], 'buf': row[3]})
    except Exception as ex:
        raise ex
    finally:
        cur.close()


# def load_img():
#     global g_img_list
#     g_img_list = [os.path.join(g_img_dir_path, filename) for filename in os.listdir(g_img_dir_path)]


def start_work():
    global g_result_list
    time.clock()

    # face = FaceBaiDu(g_source_img_info, g_img_list, g_result_list)
    face = FaceDlib(g_source_img_info, g_img_list, g_result_list)

    face.working()

    print("耗时：{0}秒".format(time.clock()))
    print('---------最终结果-------------')
    print(g_result_list)


if __name__ == '__main__':
    init()
    load_img()
    start_work()
