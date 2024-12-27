import lvgl as lv
import time
from .base_page import BasePage
import cmd

class MainPage(BasePage):
    def __init__(self, baseScreen):
        super().__init__(baseScreen)
        self.script_path = baseScreen.script_path
        self.myfont_en_100 = baseScreen.myfont_en_100
        
        # FPS计数相关
        self.last_time = 0
        self.frame_count = 0

    def init(self):
        self.genColorWheel()
        self.genSpeedNum()
        self.genTitle()
        self.genUnit()
        self.genFps()
        self.init_cmd()

    def init_cmd(self):
        self.cmd = cmd.Cmd()

    def genColorWheel(self):
        self.arc = lv.arc(self.screen)
        self.elements.append(self.arc)

        self.arc.set_style_arc_width(12, lv.PART.MAIN)
        self.arc.set_style_bg_opa(lv.OPA.TRANSP, lv.PART.KNOB)
        self.arc.set_style_arc_opa(lv.OPA.TRANSP, lv.PART.INDICATOR)
        self.setColorWheelColor(0x00a5ff)
        
        self.arc.set_bg_angles(0, 360)
        self.arc.set_value(100)
        self.arc.set_size(350, 350)
        self.arc.center()
        
        # 禁用 arc 的事件响应
        self.arc.remove_flag(lv.obj.FLAG.CLICKABLE)    # 禁用点击
        self.arc.remove_flag(lv.obj.FLAG.SCROLLABLE)   # 禁用滚动

    def setColorWheelColor(self, color_code):
        self.arc.set_style_arc_color(lv.color_hex(color_code), lv.PART.MAIN)

    def genTitle(self):
        style = self.genStyle()
        self.title_label = lv.label(self.screen)
        self.elements.append(self.title_label)
        
        self.title_label.align(lv.ALIGN.CENTER, 0, -100)
        self.title_label.set_text('Title')
        self.title_label.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN)
    
    def setTitleText(self, title):
        self.title_label.set_text(title)

    def genUnit(self):
        style = self.genStyle()
        self.unit_label = lv.label(self.screen)
        self.elements.append(self.unit_label)
        
        self.unit_label.align(lv.ALIGN.CENTER, 110, 0)
        self.unit_label.set_text('unit')
        self.unit_label.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN)

    def setUnitText(self, unit, x):
        self.unit_label.align(lv.ALIGN.CENTER, x, 0)
        self.unit_label.set_text(unit)

    def genSpeedNum(self):
        style = self.genStyle()
        self.label = lv.label(self.screen)
        self.elements.append(self.label)
        
        self.label.set_style_text_font(self.myfont_en_100, 0)
        self.label.align(lv.ALIGN.CENTER, -20, 0)
        self.label.set_text('init')
        self.label.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN)

    def set_text(self, text):
        self.label.set_text(text)
    
    def genStyle(self):
        style = lv.style_t()
        style.init()
        style.set_text_font(lv.font_montserrat_20)
        return style

    def genFps(self):
        style = self.genStyle()
        self.fps = lv.label(self.screen)
        self.elements.append(self.fps)
        
        self.fps.align(lv.ALIGN.CENTER, 0, 150)
        self.fps.set_text('fps')
        self.fps.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN)
        
        self.last_time = lv.tick_get()
        self.frame_count = 0
        
        timer = lv.timer_create(self.update_fps, 1000, None)
        self.elements.append(timer)

    def update_fps(self, task):
        current_time = lv.tick_get()
        elapsed = time.ticks_diff(current_time, self.last_time)
        
        if elapsed > 0:
            fps = (self.frame_count * 1000) / elapsed
            self.fps.set_text(f"FPS: {fps:.1f}")
            self.frame_count = 0
            self.last_time = current_time

    def event_handler(self, event):
        code = event.get_code()
        obj = event.get_target()
        if code == lv.EVENT.CLICKED:
            self.cmd.last_cmd_type = self.cmd.cmd_type
            self.cmd.cmd_type = (self.cmd.cmd_type + 1) % len(self.cmd.cmd_map)
            self.on_show(None, True)

    def on_show(self, v, init=False):            
        config_info = self.cmd.cmd_map[self.cmd.cmd_type]
        pid = bytes(config_info["pid"])
        if init:
            if pid in self.cmd.pid2value:
                v = self.cmd.pid2value[pid]
            else:
                return
        same_cmd_type = self.cmd.same_cmd_type()
        if "pid" in v:
            self.cmd.pid2value[pid] = v
            if config_info["pid"] == v["pid"]:
                if same_cmd_type and 'title' in config_info:
                    self.setTitleText(config_info["title"])
                
                mainValue = str(v['value'])
                if same_cmd_type:
                    if 'unit' in config_info:
                        x = 110
                        if len(mainValue) > 3:
                            x = 120
                        self.setUnitText(config_info["unit"], x)
                    else:
                        self.setUnitText("", 110)
                self.set_text(str(v['value'])) 