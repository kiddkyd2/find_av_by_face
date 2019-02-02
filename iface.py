import abc
import json
import time


class IFace(metaclass=abc.ABCMeta):
    def __init__(self):
        pass

    @abc.abstractmethod  # 抽象方法
    def init(self, source_img_info, target_img_list, result_list):
        return self

    @abc.abstractmethod  # 抽象方法
    def working(self):
        pass

    def save_log(self, username, data_list):
        if len(data_list) > 0:
            filename = username + '_' + time.strftime('%Y%m%d%H%M%S', time.localtime(time.time()))
            logstr = json.dumps(data_list, ensure_ascii=False)
            with open('./log/' + filename + '.log', 'w', encoding='utf-8') as f:
                f.write(logstr)

    def save_error_log(self, data_list):
        if len(data_list) > 0:
            print('处理异常的结果集合,总共：' + str(len(data_list)) + "," + json.dumps(data_list,
                                                                           ensure_ascii=False))
            filename = 'error_' + time.strftime('%Y%m%d%H%M%S', time.localtime(time.time()))
            logstr = json.dumps(data_list, ensure_ascii=False)
            with open('./log/' + filename + '.log', 'w', encoding='utf-8') as f:
                f.write(logstr)
            print('---------------------------')
