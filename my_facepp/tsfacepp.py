import configparser
import copy
import json
import os
import sys
import time
import warnings
from concurrent.futures import ThreadPoolExecutor, wait, as_completed
from operator import itemgetter
from urllib import request, parse
from urllib.request import urlopen

from iface import IFace


class FaceFacepp(IFace):

    def __init__(self):
        super().__init__()
        self.client_id = self.__get_config('facepp', 'client_id')  # client_id 为官网获取的KEY， client_secret 为官网获取的Secret
        self.client_secret = self.__get_config('facepp', 'client_secret')
        self.executor = ThreadPoolExecutor(max_workers=20)
        self.result_min_value = 0  # face++的判断是否相似的逻辑比较复杂， 建议查看文档

    def init(self, source_img_info, target_img_list, result_list):
        self.source_img_info = source_img_info
        self.target_img_list = target_img_list
        self.result_list = result_list

        self.ai_qps_error_list = []
        self.error_list = []
        self.thread_list = []

        return self

    def working(self):
        try:
            print('开始处理数据，总共：' + str(len(self.target_img_list)) + '条')
            self.__start_thread(self.target_img_list)

            while len(self.ai_qps_error_list) > 0:
                print('---------------------------')
                print('开始处理QPS超上限的数据,总共：' + str(len(self.ai_qps_error_list)) + '条')
                self.target_img_list = copy.deepcopy(self.ai_qps_error_list)  # 深度复制
                self.ai_qps_error_list.clear()
                self.__start_thread(self.target_img_list)

            if len(self.result_list) > 0:
                self.result_list.sort(key=itemgetter(2), reverse=True)

            print('---------任务完成-----------')

        except Exception as ex:
            info = sys.exc_info()
            msg = '{}:{}'.format(info[0], info[1])
            warnings.warn(msg)
        finally:
            self.executor.shutdown(False)
            self.save_log(self.source_img_info['imgurl'].split('/')[-1].split('.')[0], self.result_list, "facepp")
            self.save_error_log(self.error_list)

    # 开始构建线程进行工作
    def __start_thread(self, work_list):
        self.thread_list.clear()
        for i, img_info in enumerate(work_list):
            self.thread_list.append(self.executor.submit(self.__chk_photo_for, i, img_info))
            time.sleep(.2)  # 控制接口请求频率

        wait(self.thread_list, 30)  # 等待所有线程完成工作，30秒后继续执行代码
        self.executor.shutdown(False)
        print('---------线程结束-----------')

    def __chk_photo_for(self, i, info):
        result = self.__compare_data(info)
        print('完成：' + str(i + 1))
        if result > self.result_min_value:
            self.result_list.append((info['imgurl'], info['username'], result))

    def __compare_data(self, img_info):
        request_url = "https://api-cn.faceplusplus.com/facepp/v3/compare"

        params = {
            "api_key": self.client_id,
            "api_secret": self.client_secret,
            "image_base64_1": self.source_img_info['buf'],
            "image_base64_2": img_info['buf']
        }

        req = request.Request(url=request_url, data=parse.urlencode(params).encode(encoding='UTF8'))
        req.add_header('Content-Type', 'application/x-www-form-urlencoded')
        resp = urlopen(req, timeout=10)
        content = resp.read().decode("utf-8")
        if content:
            result = json.loads(content)

            if result and 'error_message' not in result:
                if 'confidence' not in result:
                    return -1

                confidence = float(result['confidence'])
                e4 = float(result['thresholds']['1e-4'])
                e5 = float(result['thresholds']['1e-5'])
                return confidence if confidence >= e5 else -1
            else:
                msg = result['error_message']
                if 'LIMIT' in msg:  # QPS超过限制的，添加到二次处理列表
                    self.ai_qps_error_list.append(img_info)
                    warnings.warn(msg)
                else:
                    self.error_list.append((img_info['username'], img_info['imgurl'], msg))
                    warnings.warn('当前username：' + img_info['username'] + ' imgurl：' + img_info['imgurl'] + ' ' + msg)
                return -1

    def __get_config(self, section, key):
        config = configparser.ConfigParser()
        path = os.getcwd() + '/config.conf'
        config.read(path)
        return config.get(section, key)
