import lvgl as lv

class BasePage:
    def __init__(self, baseScreen):
        self.baseScreen = baseScreen
        self.screen = baseScreen.screen
        self.page_manager = baseScreen.page_manager
        self.elements = []
        
    def init(self):
        """初始化页面，子类需要重写此方法"""
        pass
        
    def destroy(self):
        """销毁页面，清理资源"""
        for element in self.elements:
            element.delete()
        self.elements.clear()
    def show_lottie(self, obj, file_path, w, h, x, y):
        """
        显示 lottie 动画
        :param file_path: json 文件路径
        :param w: 宽度
        :param h: 高度
        :param x: x 偏移
        :param y: y 偏移
        :return: lottie 动画对象
        """
        try:
            with open(file_path, 'r') as file:
                json_data = file.read()
            json_bytes = json_data.encode('utf-8')

            lottie = lv.rlottie_create_from_raw(obj, w, h, json_bytes)
            lottie.align(lv.ALIGN.CENTER, x, y)
            return lottie
            
        except Exception as e:
            print(f"Error creating lottie animation: {e}")
            return None
