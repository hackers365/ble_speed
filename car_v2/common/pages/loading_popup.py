import lvgl as lv
from .base_page import BasePage

class LoadingPopup(BasePage):
    def __init__(self, baseScreen):
        super().__init__(baseScreen)
        self.init()
        
    def init(self):
        try:
            super().init()
            
            # 创建半透明背景
            bg = lv.obj(self.screen)
            bg.set_size(lv.pct(360), lv.pct(360))
            bg.set_style_bg_color(lv.color_hex(0x000000), 0)
            bg.set_style_bg_opa(lv.OPA._50, 0)
            bg.align(lv.ALIGN.CENTER, 0, 0)
            self.elements.append(bg)
            
            # 创建加载动画
            lottie = self.show_lottie(self.screen ,"/rlottie/loading.json", 150, 150, 0, 0)
            self.elements.append(lottie)
            
            # 创建加载文本
            label = lv.label(self.screen)
            label.set_text("Loading...")
            label.set_style_text_color(lv.color_hex(0xFFFFFF), 0)
            label.set_style_text_font(lv.font_montserrat_20, 0)
            label.align_to(lottie, lv.ALIGN.OUT_BOTTOM_MID, 0, 20)
            self.elements.append(label)
            
            # 3秒后自动关闭
            def close_popup(timer):
                self.page_manager.pop_popup()
                timer.delete()
                
            timer = lv.timer_create(close_popup, 3000, None)
            
        except Exception as e:
            print(f"Error initializing LoadingPopup: {e}") 