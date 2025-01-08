import lvgl as lv
from .base_page import BasePage

class BleModePopup(BasePage):
    def __init__(self, baseScreen):
        super().__init__(baseScreen)
        self.config = self.baseScreen.get_config()
        self.selected_mode = None
        self.save_timer = None
        self.elements = []
        
    def init(self):
        super().init()
        
        # 创建一个全屏容器
        cont = lv.obj(self.screen)
        cont.set_size(360, 360)
        cont.center()
        cont.set_style_bg_color(lv.color_hex(0xFFFFFF), 0)
        cont.set_style_radius(0, 0)
        cont.set_style_shadow_width(0, 0)
        
        # 创建标题
        title = lv.label(cont)
        title.set_text("Bluetooth Mode")
        title.align(lv.ALIGN.TOP_MID, 0, 40)
        title.set_style_text_font(lv.font_montserrat_20, 0)
        
        # 获取当前模式
        current_mode = self.config.get_run_mode()
        
        # 创建选项容器
        mode_cont = lv.obj(cont)
        mode_cont.set_size(280, 40)
        mode_cont.center()
        mode_cont.set_style_bg_opa(0, 0)  # 设置背景透明
        mode_cont.remove_flag(lv.obj.FLAG.SCROLLABLE)
        
        # 创建模式标签
        mode_label = lv.label(mode_cont)
        mode_label.set_text("Master / Slave")
        mode_label.align(lv.ALIGN.LEFT_MID, 0, 0)
        mode_label.set_style_text_font(lv.font_montserrat_20, 0)
        
        # 创建模式开关
        mode_switch = lv.switch(mode_cont)
        mode_switch.align(lv.ALIGN.RIGHT_MID, 0, 0)
        mode_switch.set_style_bg_color(lv.color_hex(0x1E90FF), lv.PART.INDICATOR | lv.STATE.CHECKED)
        
        # 设置当前选中状态
        if current_mode == 'master':
            mode_switch.add_state(lv.STATE.CHECKED)
            self.selected_mode = 'master'
        else:
            mode_switch.remove_state(lv.STATE.CHECKED)
            self.selected_mode = 'slave'
            
        # 添加开关事件
        def switch_event_handler(event):
            if mode_switch.has_state(lv.STATE.CHECKED):
                self.selected_mode = 'master'
            else:
                self.selected_mode = 'slave'
                
        mode_switch.add_event_cb(switch_event_handler, lv.EVENT.VALUE_CHANGED, None)
        
        # 创建保存按钮
        save_button = lv.button(cont)
        save_button.set_size(100, 40)
        save_button.align(lv.ALIGN.BOTTOM_MID, 0, -60)
        save_button.set_style_bg_color(lv.color_hex(0x1E90FF), 0)
        save_button.set_style_radius(16, 0)
        
        save_label = lv.label(save_button)
        save_label.set_text("Save")
        save_label.center()
        save_label.set_style_text_font(lv.font_montserrat_20, 0)
        save_label.set_style_text_color(lv.color_hex(0xFFFFFF), 0)
        
        # 添加保存按钮事件
        def save_event_handler(e):
            try:
                if self.selected_mode:
                    self.config.set_run_mode(self.selected_mode)
                    def complete():
                        self.page_manager.pop_popup()
                    self.show_msgbox("Save Success", timeout=1000, user_callback=complete)
            except Exception as e:
                self.show_msgbox(f"Save Failed: {str(e)}", timeout=2000)
                
        save_button.add_event_cb(save_event_handler, lv.EVENT.CLICKED, None)
        
        # 将所有元素添加到elements列表中
        self.elements.extend([cont])

    def destroy(self):
        """重写销毁方法"""
        if self.save_timer:
            self.save_timer.delete()
            self.save_timer = None
        super().destroy()