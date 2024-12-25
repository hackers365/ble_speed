import lvgl as lv
from .base_page import BasePage

class SecondPage(BasePage):
    def __init__(self, screen):
        print("SecondPage __init__ called")  # 调试信息
        super().__init__(screen.container)  # 使用 container 作为 screen
        self.screen = screen.container  # 确保使用正确的容器
        
    def init(self):
        try:
            print("SecondPage init started")  # 调试信息
            super().init()
            
            # 创建个大标签
            label = lv.label(self.screen)
            label.set_text("Second Page")
            label.center()
            # 设置字体大小和颜色
            label.set_style_text_font(lv.font_montserrat_20, 0)
            label.set_style_text_color(lv.color_hex(0x00ff00), 0)  # 绿色
            self.elements.append(label)
            print("Main label created")  # 调试信息
            
            # 添加一些额外的元素以区分页面
            info_label = lv.label(self.screen)
            info_label.set_text("Swipe left/right to switch pages")
            info_label.align(lv.ALIGN.CENTER, 0, 50)
            self.elements.append(info_label)
            print("Info label created")  # 调试信息
            
        except Exception as e:
            print(f"Error initializing SecondPage: {e}") 