
import usys as sys
sys.path.append('') # See: https://github.com/micropython/micropython/issues/6419

import micropython,gc

import time
# Initialize
from hardware import display,touch

import lvgl as lv
import lvgl_esp32

import fs_driver

import cmd

class Screen():
    def __init__(self):
        self.init_screen()
        self.init_font()
        self.init_cmd()
        self.run()
    def run(self):
        self.genColorWheel()
        self.genSpeedNum()
    def init_cmd(self):
        self.cmd = cmd.Cmd()
    def init_screen(self):
        wrapper = lvgl_esp32.Wrapper(display,touch)
        wrapper.init()

        # 设置显示
        display.brightness(60)
        display.swapXY(False)
        display.mirrorX(True)
        display.mirrorY(True)

        touch.swapXY(False)
        touch.mirrorX(True)
        touch.mirrorY(True)

        # 创建屏幕和设置背景
        self.screen = lv.screen_active()
        self.screen.set_style_bg_color(lv.color_hex(0x000000), lv.PART.MAIN | lv.STATE.DEFAULT)
        self.screen.set_style_bg_opa(255, lv.PART.MAIN | lv.STATE.DEFAULT)
    def init_font(self):
        try:
            script_path = __file__[:__file__.rfind('/')] if __file__.find('/') >= 0 else '.'
        except NameError:
            script_path = ''

        fs_drv = lv.fs_drv_t()
        fs_driver.fs_register(fs_drv, 'S')

        #myfont_en_150 = lv.binfont_create("S:%s/font/speed_num_consolas_150.bin" % script_path)
        self.myfont_en_100 = lv.binfont_create("S:%s/font/speed_num_consolas_100.bin" % script_path)

    def genColorWheel(self):
        scr = self.screen
        self.arc = lv.arc(scr)

        self.arc.set_style_arc_width(20, lv.PART.MAIN) #外框宽度

        self.arc.set_style_bg_opa(lv.OPA.TRANSP, lv.PART.KNOB) #删掉尾巴
        self.arc.set_style_arc_opa(lv.OPA.TRANSP, lv.PART.INDICATOR) #隐藏上层

        #设置底层颜色, 初始化黄色
        self.setColorWheelColor(0x00a5ff)      

        self.arc.set_bg_angles(0, 360)   #背景圆环最大角度
        self.arc.set_value(100)          #值，默认0-100
        self.arc.set_size(350,350)       #宽高
        self.arc.center()                #中间
        self.arc.add_event_cb(self.event_handler, lv.EVENT.CLICKED, None)
    def setColorWheelColor(self, color_code):  #不是rgv, 是bgr
        self.arc.set_style_arc_color(lv.color_hex(color_code), lv.PART.MAIN)
    
    def genSpeedNum(self):
        scr = self.screen
        style = self.genStyle()
        self.label = lv.label(scr)
        self.label.set_style_text_font(self.myfont_en_100, 0)  # set the font
        self.label.align(lv.ALIGN.CENTER, 0, 0)
        self.label.set_text('init')
        self.label.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN)
        
        #self.label.add_event_cb(event_handler, lv.EVENT.ALL, None)
        #label.add_style(style, lv.PART.MAIN)
    
    def set_text(self, text):
        #self.label.set_style_text_font(myfont_en_150, 0)  # set the font
        self.label.set_text(text)
    
    def genStyle(self):
        # 创建一个新的样式，用于设置文字大小
        style = lv.style_t()
        style.init()

        # 设置文字大小，比如设置为20像素
        #style.set_text_font(lv.STATE.DEFAULT, lv.font_montserrat_16)
        style.set_text_font(lv.font_montserrat_20)
        return style

    def on_show(self, v):
        scr = self.screen
        config_info = self.cmd.cmd_map[self.cmd.cmd_type]
        if "pid" in v:
            print(config_info["pid"] == v["pid"])
            if config_info["pid"] == v["pid"]:
                if v["pid"] == '0D':
                    if type(v['value']) != int:
                        print("speed is not int")
                        return
                    if v['value'] <= 40:
                        self.setColorWheelColor(0x90EE90)
                    elif v['value'] <= 60:
                        self.setColorWheelColor(0x00D7FF)
                    elif v['value'] <= 80:
                        self.setColorWheelColor(0xFFBF00)
                    elif v['value'] <= 120:
                        self.setColorWheelColor(0x0045FF)
                    else:
                        self.setColorWheelColor(0x0000FF)
                else:
                    self.setColorWheelColor(0x00a5ff)
                self.set_text(str(v['value']))

    def event_handler(self, event):
        code = event.get_code()
        obj = event.get_target()
        if code == lv.EVENT.CLICKED:
            self.cmd.cmd_type = (self.cmd.cmd_type + 1) % len(self.cmd.cmd_map)

def Run():
    screen = Screen()
    resp = {"pid": '0D', 'value': 100}
    screen.on_show(resp)
    while True:
        lv.timer_handler_run_in_period(5)
        time.sleep(0.1)
#if __name__ == '__main__':
#    Run()

