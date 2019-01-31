import configparser
import json
import os
import sys
import time
import warnings
from concurrent.futures import ThreadPoolExecutor, wait
from operator import itemgetter
from urllib import request
from urllib.request import urlopen

from iface import IFace


class FaceBaiDu(IFace):
    def __init__(self, source_img_info, target_img_list, result_list):
        super().__init__(source_img_info, target_img_list, result_list)
        self.client_id = self.__get_config('baidu', 'client_id')  # client_id 为官网获取的AK， client_secret 为官网获取的SK
        self.client_secret = self.__get_config('baidu', 'client_secret')
        self.executor = ThreadPoolExecutor(max_workers=10)

        self.source_img_info = source_img_info
        self.target_img_list = target_img_list
        self.result_list = result_list
        self.result_min_value = 50

        self.ai_qps_error_list = []
        self.error_list = []
        self.thread_list = []

    def working(self):
        print('开始处理数据，总共：' + str(len(self.target_img_list)) + '条')
        for i, target_info in enumerate(self.target_img_list):
            print('当前：' + str(i + 1))
            self.thread_list.append(self.executor.submit(self.__chk_photo_for, target_info))
            # threading.Thread(target=chk_photo_for, args=(info,)).start()
            time.sleep(.6)

        try:
            if len(self.ai_qps_error_list) > 0:
                print('---------------------------')
                print('开始处理QPS超上限的数据,总共：' + str(len(self.ai_qps_error_list)) + '条')
                for i, info in enumerate(self.ai_qps_error_list):
                    print('当前：' + str(i + 1))
                    self.thread_list.append(self.executor.submit(self.__chk_photo_for, info))
                    # threading.Thread(target=chk_photo_for, args=(info,)).start()
                    time.sleep(.6)

            self.result_list.sort(key=itemgetter(2), reverse=True)

            wait(self.thread_list, return_when='ALL_COMPLETED', timeout=60)

            print('---------------------------')
            if len(self.error_list) > 0:
                print('处理异常的结果集合,总共：' + str(len(self.error_list)) + "," + json.dumps(self.error_list,
                                                                                   ensure_ascii=False))
                self.__save_error_log()
                print('---------------------------')

        except Exception as ex:
            info = sys.exc_info()
            msg = '{}:{}'.format(info[0], info[1])
            warnings.warn(msg)
        finally:
            self.executor.shutdown()
            self.__save_log()

    def __get_config(self, section, key):
        config = configparser.ConfigParser()
        path = os.getcwd() + '/config.conf'
        config.read(path)
        return config.get(section, key)

    def __get_token(self):
        host = 'https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id=' + self.client_id + \
               '&client_secret=' + self.client_secret
        req = request.Request(host)
        req.add_header('Content-Type', 'application/json; charset=UTF-8')
        resp = urlopen(req)
        content = resp.read().decode('utf-8')
        if content:
            # 转化为字典
            content = eval(content)
            token = content['access_token']
            return token
        else:
            raise RuntimeError(content)

    def __chk_photo_for(self, info):
        result = self.__compare_data(info)
        if result > self.result_min_value:
            self.result_list.append((info['imgurl'], info['username'], result))

    def __compare_data(self, info):
        request_url = "https://aip.baidubce.com/rest/2.0/face/v3/match"

        params = json.dumps(
            [{"image": self.source_img_info['buf'], "image_type": "BASE64", "face_type": "LIVE",
              "quality_control": "LOW"},
             {"image": info['buf'], "image_type": "BASE64", "face_type": "LIVE", "quality_control": "LOW"}])

        request_url = request_url + "?access_token=" + self.__get_token()
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
                    self.ai_qps_error_list.append(info)
                    warnings.warn(msg)
                else:
                    self.error_list.append((info['username'], info['imgurl'], msg))
                    warnings.warn('当前username：' + info['username'] + ' imgurl：' + info['imgurl'] + ' ' + msg)
                return -1

    def __save_log(self):
        username = self.source_img_info['imgurl'].split('/')[-1].split('.')[0]
        filename = username + '_' + time.strftime('%Y%m%d%H%M%S', time.localtime(time.time()))
        logstr = json.dumps(self.result_list, ensure_ascii=False)
        with open('./log/' + filename + '.log', 'w', encoding='utf-8') as f:
            f.write(logstr)

    def __save_error_log(self):
        filename = 'error_' + time.strftime('%Y%m%d%H%M%S', time.localtime(time.time()))
        logstr = json.dumps(self.error_list, ensure_ascii=False)
        with open('./log/' + filename + '.log', 'w', encoding='utf-8') as f:
            f.write(logstr)
