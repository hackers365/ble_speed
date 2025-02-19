import lvgl as lv
from .base_page import BasePage

class BleModePopup(BasePage):
    def __init__(self, baseScreen):
        super().__init__(baseScreen)
        self.config = self.baseScreen.get_config()
        self.selected_mode = None
        self.save_timer = None
        self.elements = []
        
    def create_option_item(self, parent, text, y_offset=0):
        """创建统一样式的选项项"""
        item = lv.obj(parent)
        item.set_size(280, 50)  # 增加高度提高点击区域
        item.align(lv.ALIGN.TOP_MID, 0, y_offset)
        item.set_style_bg_opa(0, 0)
        item.set_style_pad_all(0, 0)
        
        # 添加点击效果
        item.set_style_bg_color(lv.color_hex(0xeeeeee), lv.STATE.PRESSED)
        item.set_style_bg_opa(lv.OPA._20, lv.STATE.PRESSED)
        
        label = lv.label(item)
        label.set_text(text)
        label.align(lv.ALIGN.LEFT_MID, 10, 0)  # 添加左边距
        label.set_style_text_font(lv.font_montserrat_20, 0)
        
        switch = lv.switch(item)
        switch.align(lv.ALIGN.RIGHT_MID, -10, 0)  # 添加右边距
        switch.set_style_bg_color(lv.color_hex(0x1E90FF), lv.PART.INDICATOR | lv.STATE.CHECKED)
        
        return item, switch

    def init(self):
        super().init()
        
        # 创建一个全屏容器
        cont = lv.obj(self.screen)
        cont.set_size(360, 360)
        cont.center()
        cont.set_style_bg_color(lv.color_hex(0xFFFFFF), 0)
        cont.set_style_radius(0, 0)
        cont.set_style_shadow_width(0, 0)
        cont.set_style_pad_all(0, 0)
        
        # LVGL 9.1的布局设置
        cont.set_flex_flow(lv.FLEX_FLOW.COLUMN)
        cont.set_flex_align(
            lv.FLEX_ALIGN.START,
            lv.FLEX_ALIGN.CENTER,
            lv.FLEX_ALIGN.CENTER
        )
        
        # 创建标题
        title = lv.label(cont)
        title.set_text("Bluetooth Mode")
        title.set_style_text_font(lv.font_montserrat_20, 0)
        title.set_style_pad_ver(40, 0)
        
        # 获取当前配置
        current_mode = self.config.get_run_mode()
        current_show_image = self.config.get_show_image()
        current_obd_espnow = self.config.get_obd_espnow() if hasattr(self.config, 'get_obd_espnow') else False
        
        # 创建选项容器
        options_cont = lv.obj(cont)
        options_cont.set_size(280, 200)  # 增加高度
        options_cont.set_style_bg_opa(0, 0)
        options_cont.set_style_pad_all(0, 0)
        options_cont.remove_flag(lv.obj.FLAG.SCROLLABLE)
        options_cont.set_flex_grow(1)
        
        # 创建三个选项
        mode_item, mode_switch = self.create_option_item(options_cont, "Master / Slave", 0)
        image_item, image_switch = self.create_option_item(options_cont, "Show Image", 60)
        obd_item, obd_switch = self.create_option_item(options_cont, "OBD Req ESPNOW", 120)
        
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
            
        if current_obd_espnow:
            obd_switch.add_state(lv.STATE.CHECKED)
        else:
            obd_switch.remove_state(lv.STATE.CHECKED)
            
        # 创建保存按钮
        save_button = lv.button(cont)
        save_button.set_size(140, 50)
        save_button.set_style_bg_color(lv.color_hex(0x1E90FF), 0)
        save_button.set_style_radius(20, 0)
        save_button.set_style_pad_ver(20, 0)
        
        save_label = lv.label(save_button)
        save_label.set_text("Save")
        save_label.center()
        save_label.set_style_text_font(lv.font_montserrat_20, 0)
        save_label.set_style_text_color(lv.color_hex(0xFFFFFF), 0)
        
        # 添加保存按钮事件
        def save_event_handler(e):
            try:
                selected_mode = 'master' if mode_switch.has_state(lv.STATE.CHECKED) else 'slave'
                self.config.set_run_mode(selected_mode)
                self.config.set_show_image(image_switch.has_state(lv.STATE.CHECKED))
                self.config.set_obd_espnow(obd_switch.has_state(lv.STATE.CHECKED))
                def complete():
                    self.page_manager.pop_popup()
                self.show_msgbox("Save Success", timeout=1000, user_callback=complete)
            except Exception as e:
                self.show_msgbox(f"Save Failed: {str(e)}", timeout=2000)
                
        save_button.add_event_cb(save_event_handler, lv.EVENT.CLICKED, None)
        
        self.elements.extend([cont])

    def destroy(self):
        """重写销毁方法"""
        if self.save_timer:
            self.save_timer.delete()
            self.save_timer = None
        super().destroy()