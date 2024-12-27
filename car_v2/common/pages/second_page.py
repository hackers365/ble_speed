import lvgl as lv
from .base_page import BasePage
from .loading_popup import LoadingPopup

class SecondPage(BasePage):
    def __init__(self, baseScreen):
        super().__init__(baseScreen)
        
    def init(self):
        try:
            super().init()
            
            # 创建菜单项列表
            menu_items = [
                {"text": "Baby", "callback": self.on_baby_click},
                {"text": "Loading", "callback": self.on_loading_click}
            ]
            
            # 计算按钮的大小和位置
            btn_width = 280  # 按钮宽度
            btn_height = 60  # 按钮高度
            spacing = 20     # 按钮之间的间距
            
            # 创建菜单按钮
            for i, item in enumerate(menu_items):
                # 创建按钮容器
                btn = lv.button(self.screen)
                btn.set_size(btn_width, btn_height)
                # 垂直居中对齐，根据索引计算y偏移
                y_offset = (i - (len(menu_items) - 1) / 2) * (btn_height + spacing)
                btn.align(lv.ALIGN.CENTER, 0, int(y_offset))
                
                # 设置按钮样式
                btn.set_style_bg_color(lv.color_hex(0x1E90FF), 0)  # 设置背景色
                btn.set_style_bg_opa(lv.OPA.COVER, 0)             # 设置不透明度
                btn.set_style_radius(10, 0)                        # 设置圆角
                btn.set_style_shadow_width(10, 0)                  # 添加阴影
                btn.set_style_shadow_color(lv.color_hex(0x1E90FF), 0)
                btn.set_style_shadow_opa(lv.OPA._40, 0)
                
                # 创建按钮文本标签
                label = lv.label(btn)
                label.set_text(item["text"])
                label.center()
                label.set_style_text_font(lv.font_montserrat_20, 0)
                label.set_style_text_color(lv.color_hex(0xFFFFFF), 0)
                
                # 添加点击事件
                btn.add_event_cb(item["callback"], lv.EVENT.CLICKED, None)
                
                # 将按钮添加到元素列表中
                self.elements.append(btn)
                
        except Exception as e:
            print(f"Error initializing SecondPage: {e}")
            
    def on_baby_click(self, event):
        """Baby 按钮点击回调"""
        try:
            # 隐藏所有现有元素
            for element in self.elements:
                element.set_style_opa(0, 0)  # 设置透明度为0来隐藏元素
            
            # 显示 lottie 动画
            lottie = self.show_lottie("/rlottie/loading.json", 150, 150, 0, 0)
            self.elements.append(lottie)  # 将动画添加到元素列表中
            
            # 创建定时器来恢复按钮颜色和删除动画
            def cleanup(timer):
                # 恢复所有元素的显示
                for element in self.elements:
                    if element != lottie:  # 不恢复动画的显示
                        element.set_style_opa(255, 0)  # 设置透明度为255来显示元素
                
                if lottie in self.elements:
                    lottie.delete()
                    self.elements.remove(lottie)
                timer.delete()
            
            timer = lv.timer_create(cleanup, 3000, None)  # 3秒后清理
            
            print("Baby button clicked")
            
        except Exception as e:
            print(f"Error in baby click handler: {e}")
            
    def on_loading_click(self, event):
        """Loading 按钮点击回调"""
        try:
            # 创建功能页面
            loading_popup = LoadingPopup(self.baseScreen)
            # 使用 PageManager 压入功能页面
            self.baseScreen.page_manager.push_popup(loading_popup)
            
        except Exception as e:
            print(f"Error in loading click handler: {e}") 