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
        current_show_image = self.config.get_show_image()
        
        # 创建选项容器
        options_cont = lv.obj(cont)
        options_cont.set_size(280, 120)
        options_cont.align(lv.ALIGN.TOP_MID, 0, 100)
        options_cont.set_style_bg_opa(0, 0)
        options_cont.remove_flag(lv.obj.FLAG.SCROLLABLE)
        
        # 创建模式选项
        mode_item = lv.obj(options_cont)
        mode_item.set_size(280, 40)
        mode_item.align(lv.ALIGN.TOP_MID, 0, 0)
        mode_item.set_style_bg_opa(0, 0)
        mode_item.remove_flag(lv.obj.FLAG.SCROLLABLE)
        
        mode_label = lv.label(mode_item)
        mode_label.set_text("Master / Slave")
        mode_label.align(lv.ALIGN.LEFT_MID, 0, 0)
        mode_label.set_style_text_font(lv.font_montserrat_20, 0)
        
        mode_switch = lv.switch(mode_item)
        mode_switch.align(lv.ALIGN.RIGHT_MID, 0, 0)
        mode_switch.set_style_bg_color(lv.color_hex(0x1E90FF), lv.PART.INDICATOR | lv.STATE.CHECKED)
        
        # 创建显示图片选项
        image_item = lv.obj(options_cont)
        image_item.set_size(280, 40)
        image_item.align(lv.ALIGN.TOP_MID, 0, 60)
        image_item.set_style_bg_opa(0, 0)
        image_item.remove_flag(lv.obj.FLAG.SCROLLABLE)
        
        image_label = lv.label(image_item)
        image_label.set_text("Show Image")
        image_label.align(lv.ALIGN.LEFT_MID, 0, 0)
        image_label.set_style_text_font(lv.font_montserrat_20, 0)
        
        image_switch = lv.switch(image_item)
        image_switch.align(lv.ALIGN.RIGHT_MID, 0, 0)
        image_switch.set_style_bg_color(lv.color_hex(0x1E90FF), lv.PART.INDICATOR | lv.STATE.CHECKED)
        
        # 设置当前选中状态
        if current_mode == 'master':
            mode_switch.add_state(lv.STATE.CHECKED)
            self.selected_mode = 'master'
        else:
            mode_switch.remove_state(lv.STATE.CHECKED)
            self.selected_mode = 'slave'
            
        if current_show_image:
            image_switch.add_state(lv.STATE.CHECKED)
        else:
            image_switch.remove_state(lv.STATE.CHECKED)
            
        # 创建保存按钮
        save_button = lv.button(cont)
        save_button.set_size(140, 50)
        save_button.align(lv.ALIGN.BOTTOM_MID, 0, -40)
        save_button.set_style_bg_color(lv.color_hex(0x1E90FF), 0)
        save_button.set_style_radius(20, 0)
        
        save_label = lv.label(save_button)
        save_label.set_text("Save")
        save_label.center()
        save_label.set_style_text_font(lv.font_montserrat_20, 0)
        save_label.set_style_text_color(lv.color_hex(0xFFFFFF), 0)
        
        # 添加保存按钮事件
        def save_event_handler(e):
            try:
                # 获取当前开关状态来决定模式
                selected_mode = 'master' if mode_switch.has_state(lv.STATE.CHECKED) else 'slave'
                self.config.set_run_mode(selected_mode)
                self.config.set_show_image(image_switch.has_state(lv.STATE.CHECKED))
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