import abc


class IFace(metaclass=abc.ABCMeta):
    def __init__(self, source_img_info, target_img_list, result_list):
        pass

    @abc.abstractmethod  # 抽象方法
    def working(self):
        pass
