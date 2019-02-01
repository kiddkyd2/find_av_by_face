# -*- coding: utf-8 -*-
import base64
import json
import sys
import time
import warnings
from concurrent.futures import ThreadPoolExecutor, wait, as_completed
from operator import itemgetter

import dlib
import cv2
import os
import glob

import numpy as np

from iface import IFace


class FaceDlib(IFace):
    def __init__(self):
        super().__init__()
        self.current_path = os.getcwd()  # 获取根路径
        self.predictor_path = self.current_path + "/my_dlib/model/shape_predictor_68_face_landmarks.dat"
        self.face_rec_model_path = self.current_path + "/my_dlib/model/dlib_face_recognition_resnet_model_v1.dat"
        self.dataPath = self.current_path + "/my_dlib/cache_data/"
        # 读入模型
        self.detector = dlib.get_frontal_face_detector()
        self.shape_predictor = dlib.shape_predictor(self.predictor_path)
        self.face_rec_model = dlib.face_recognition_model_v1(self.face_rec_model_path)

        self.executor = ThreadPoolExecutor(max_workers=8)
        self.result_min_value = 0.4  # 至少要少于0.6才是相似

    def init(self, source_img_info, target_img_list, result_list):
        os.makedirs(os.path.join(self.current_path, 'my_dlib/cache_data/'), exist_ok=True)

        self.result_list = result_list
        self.source_img_info = source_img_info
        self.target_img_list = target_img_list
        self.source_img_data = self.__get_tezheng(source_img_info)

        self.error_list = []
        self.thread_list = []

        return self

    def working(self):
        # pass
        print('开始处理数据，总共：' + str(len(self.target_img_list)) + '条')
        for i, target_info in enumerate(self.target_img_list):
            self.thread_list.append(self.executor.submit(self.__chk_photo_for, target_info))

        try:
            for i, future in enumerate(as_completed(self.thread_list)):
                print('完成：' + str(i + 1))
            # wait(self.thread_list, return_when='ALL_COMPLETED')

            if len(self.result_list) > 0:
                self.result_list.sort(key=itemgetter(2))
            print('---------线程结束------------')
        except Exception as ex:
            info = sys.exc_info()
            msg = '{}:{}'.format(info[0], info[1])
            warnings.warn(msg)
        finally:
            self.executor.shutdown()
            self.__save_log()
            self.__save_error_log()

    def __chk_photo_for(self, target_info):
        result = self.__compare_data(self.source_img_data, self.__get_tezheng(target_info))
        if result < self.result_min_value:
            self.result_list.append((target_info['imgurl'], target_info['username'], result))

    def __get_tezheng(self, img_info):

        # 检查是否有缓存数据
        filePath = self.dataPath + img_info['imgurl'].split('/')[-1].split('.')[0] + '_' + img_info["username"] + '.npy'
        if os.path.isfile(filePath):
            vectors = np.load(filePath)
            if vectors.size > 0:
                return vectors

        # 没有的话，就构建并存起来
        img_data = base64.b64decode(img_info['buf'])
        img_array = np.fromstring(img_data, np.uint8)
        img = cv2.imdecode(img_array, cv2.COLOR_BGR2RGB)
        dets = self.detector(img, 1)  # 人脸标定

        if len(dets) is not 1:
            warnings.warn("图片检测的人脸数为: {}".format(len(dets)))
            self.error_list.append((img_info['username'], img_info['imgurl']))
            return np.array([])

        face = dets[0]
        shape = self.shape_predictor(img, face)
        vectors = np.array([])
        for i, num in enumerate(self.face_rec_model.compute_face_descriptor(img, shape)):
            vectors = np.append(vectors, num)
        np.save(filePath, vectors)
        return vectors

    # 计算欧式距离，判断是否是同一个人
    def __compare_data(self, data1, data2):
        diff = 0
        # for v1, v2 in data1, data2:
        # diff += (v1 - v2)**2
        for i in range(len(data1)):
            diff += (data1[i] - data2[i]) ** 2
        diff = np.sqrt(diff)
        return diff

    def __save_log(self):
        username = self.source_img_info['imgurl'].split('/')[-1].split('.')[0]
        filename = username + '_' + time.strftime('%Y%m%d%H%M%S', time.localtime(time.time()))
        logstr = json.dumps(self.result_list, ensure_ascii=False)
        with open('./log/' + filename + '.log', 'w', encoding='utf-8') as f:
            f.write(logstr)

    def __save_error_log(self):
        if len(self.error_list) > 0:
            print('处理异常的结果集合,总共：' + str(len(self.error_list)) + "," + json.dumps(self.error_list,
                                                                                 ensure_ascii=False))
            filename = 'error_' + time.strftime('%Y%m%d%H%M%S', time.localtime(time.time()))
            logstr = json.dumps(self.error_list, ensure_ascii=False)
            with open('./log/' + filename + '.log', 'w', encoding='utf-8') as f:
                f.write(logstr)
            print('---------------------------')
