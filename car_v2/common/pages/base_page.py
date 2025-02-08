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
        print(self.elements)
        for element in self.elements:
            element.delete()
        self.elements.clear()
    def show_lottie(self, obj, file_path, w, h, x, y, timeOut=None):
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
            if timeOut:
                timer = lv.timer_create(lambda t: lottie.delete(), timeOut, None)
                timer.set_repeat_count(1)
            return lottie
            
        except Exception as e:
            print(f"Error creating lottie animation: {e}")
            return None
    def get_dma_size(self):
        print(self.baseScreen.wrapper.get_dma_size())

    def show_msgbox(self, msg, title=None, timeout=2000, user_callback=None):
        """
        显示消息框
        :param title: 标题
        :param msg: 消息内容
        :param timeout: 自动关闭时间(毫秒)，默认2秒
        """
        mbox = lv.msgbox(self.screen)
        
        # 设置标题和内容
        if title:
            mbox.add_title(title)
        mbox.add_text(msg)
        
        # 设置整体样式
        mbox.set_style_bg_color(lv.color_hex(0xFFFFFF), lv.PART.MAIN)  # 白色背景
        mbox.set_style_border_color(lv.color_hex(0xE0E0E0), lv.PART.MAIN)  # 浅灰色边框
        mbox.set_style_border_width(2, lv.PART.MAIN)
        mbox.set_style_radius(10, lv.PART.MAIN)
        mbox.set_style_shadow_width(20, lv.PART.MAIN)
        mbox.set_style_shadow_color(lv.color_hex(0x000000), lv.PART.MAIN)
        mbox.set_style_shadow_opa(30, lv.PART.MAIN)  # 降低阴影透明度
        mbox.set_style_pad_all(20, lv.PART.MAIN)
        
        # 设置文字样式
        mbox.set_style_text_color(lv.color_hex(0x333333), lv.PART.MAIN)  # 深灰色文字
        mbox.set_style_text_font(lv.font_montserrat_20, lv.PART.MAIN)
        mbox.set_style_text_align(lv.TEXT_ALIGN.CENTER, lv.PART.MAIN)
        
        # 如果有标题，设置标题样式
        '''
        if title:
            mbox.set_style_text_font(lv.font_montserrat_20, lv.PART.TITLE)
            mbox.set_style_pad_bottom(15, lv.PART.TITLE)
            mbox.set_style_text_align(lv.TEXT_ALIGN.CENTER, lv.PART.TITLE)
            mbox.set_style_text_color(lv.color_hex(0x222222), lv.PART.TITLE)  # 标题文字颜色
        '''

        # 调整内容区域样式
        mbox.set_style_pad_ver(20, lv.PART.MAIN)
        mbox.set_style_pad_hor(30, lv.PART.MAIN)
        
        mbox.center()
        def complete(t):
            mbox.delete()
            if user_callback:
                user_callback()
        # 设置定时器自动关闭
        timer = lv.timer_create(complete, timeout, None)
        timer.set_repeat_count(1)
