import base64
import configparser
import json
import os
import sqlite3
import sys
import threading
import time
import warnings
from datetime import datetime
from operator import itemgetter
from urllib import request
# client_id 为官网获取的AK， client_secret 为官网获取的SK
from urllib.request import urlopen

import redis


def get_config(section, key):
    config = configparser.ConfigParser()
    path = os.path.split(os.path.realpath(__file__))[0] + '/config.conf'
    config.read(path)
    return config.get(section, key)


client_id = get_config('baidu', 'client_id')
client_secret = get_config('baidu', 'client_secret')
r = redis.Redis(host='localhost', port=6379, db=0)
conn = sqlite3.connect(get_config('db', 'path'))
cur = conn.cursor()

g_source_img = './source_img/angelababy.jpg'
g_result_min_value = 60
g_img_list = []
g_ai_resultlist = []
g_ai_qps_errorlist = []
g_ai_errorlist = []


def get_token():
    token_key = 'baiduToken'
    if r.exists(token_key):
        return r.get(token_key).decode()
    else:
        host = 'https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id=' + client_id + \
               '&client_secret=' + client_secret
        req = request.Request(host)
        req.add_header('Content-Type', 'application/json; charset=UTF-8')
        resp = urlopen(req)
        content = resp.read().decode('utf-8')
        if content:
            # 转化为字典
            content = eval(content)
            token = content['access_token']
            r.set('baiduToken', token, ex=60 * 60 * 24 * 30)  # 缓存30天
            return token
        else:
            raise RuntimeError(content)


def load_img():
    try:
        rows = cur.execute("select * from face_youma")
        for row in rows:
            g_img_list.append({'imgurl': row[0], 'username': row[1], 'videourl': row[2], 'buf': row[3]})
    except Exception as ex:
        raise ex
    finally:
        cur.close()


# def load_img():
#     global g_img_list
#     g_img_list = [os.path.join(g_img_dir_path, filename) for filename in os.listdir(g_img_dir_path)]


def chk_photo(info):
    def base64photo(img_path):
        with open(img_path, "rb") as f:
            base64_data = base64.b64encode(f.read())
            return bytes.decode(base64_data)

    request_url = "https://aip.baidubce.com/rest/2.0/face/v3/match"

    params = json.dumps(
        [{"image": base64photo(g_source_img), "image_type": "BASE64", "face_type": "LIVE", "quality_control": "LOW"},
         {"image": info['buf'], "image_type": "BASE64", "face_type": "LIVE", "quality_control": "LOW"}])

    request_url = request_url + "?access_token=" + get_token()
    req = request.Request(url=request_url, data=params.encode(encoding='UTF8'))
    req.add_header('Content-Type', 'application/json')
    resp = urlopen(req)
    content = resp.read().decode("utf-8")
    if content:
        result = json.loads(content)
        msg = result['error_msg']
        if result and msg == 'SUCCESS':
            return float(result['result']['score'])
        else:
            if 'qps' in msg:  # QPS超过百度限制的，添加到二次处理列表
                g_ai_qps_errorlist.append(info)
                warnings.warn(msg)
            else:
                info['buf'] = '' # 清空buf，比较一会打印的时候json太长
                g_ai_errorlist.append(info)
                warnings.warn('当前username：' + info['username'] + ' imgurl：' + info['imgurl'] + ' ' + msg)
            return -1


def chk_photo_for(info):
    result = chk_photo(info)
    if result > g_result_min_value:
        g_ai_resultlist.append((info['imgurl'], info['username'], result))


def start_work():
    time.clock()
    print('开始处理数据，总共：' + str(len(g_img_list)) + '条')
    for i, info in enumerate(g_img_list):
        print('当前：' + str(i + 1))
        threading.Thread(target=chk_photo_for, args=(info,)).start()
        time.sleep(.6)

    try:
        if len(g_ai_qps_errorlist) > 0:
            print('---------------------------')
            print('开始处理QPS超上限的数据,总共：' + str(len(g_ai_qps_errorlist)) + '条')
            for i, info in enumerate(g_ai_qps_errorlist):
                print('当前：' + str(i))
                threading.Thread(target=chk_photo_for, args=(info,)).start()
                time.sleep(.6)

        g_ai_resultlist.sort(key=itemgetter(2), reverse=True)

    except Exception as ex:
        info = sys.exc_info()
        msg = '{}:{}'.format(info[0], info[1])
        warnings.warn(msg)
    finally:
        save_log()

    print(g_ai_resultlist)
    print("耗时：{0}秒".format(time.clock()))
    print('---------------------------')
    if len(g_ai_errorlist) > 0:
        print('处理异常的结果集合,总共：' + str(len(g_ai_errorlist)) + "," + json.dumps(g_ai_errorlist))
    print('---------------------------')


def save_log():
    username = g_source_img.split('/')[-1].split('.')[0]
    filename = username + '_' + time.strftime('%Y%m%d%H%M%S', time.localtime(time.time()))
    logstr = json.dumps(g_ai_resultlist, ensure_ascii=False)
    with open('./log/' + filename + '.log', 'w', encoding='utf-8') as f:
        f.write(logstr)


if __name__ == '__main__':
    load_img()
    start_work()
