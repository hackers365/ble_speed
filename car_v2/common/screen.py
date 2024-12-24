
import usys as sys
sys.path.append('/common') # See: https://github.com/micropython/micropython/issues/6419

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
        self.genTitle()
        self.genUnit()
        #self.setBreath()
        #self.setImage()
        self.genFps()
        #self.show_lottie("/rlottie/smile.json", 100, 100, 0, 0)
        #self.show_lottie("/rlottie/loading.json", 100, 100, -100, 0)
        #self.show_lottie("/rlottie/rainbow.json", 100, 100, 100, 0)
        
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
        self.script_path = script_path
        fs_drv = lv.fs_drv_t()
        fs_driver.fs_register(fs_drv, 'S')

        #myfont_en_150 = lv.binfont_create("S:%s/font/speed_num_consolas_150.bin" % script_path)
        self.myfont_en_100 = lv.binfont_create("S:%s/common/font/speed_num_consolas_100.bin" % script_path)
    
    def setImage(self):
        with open('%s/common/car.png' % self.script_path, 'rb') as f:
            png_data = f.read()
        
        png_image_dsc = lv.image_dsc_t({
            'data_size': len(png_data),
            'data': png_data 
        })

        # Create an image using the decoder
        image1 = lv.image(self.screen)
        image1.set_src(png_image_dsc)
        image1.set_pos(100,240)
    def genColorWheel(self):
        scr = self.screen
        self.arc = lv.arc(scr)

        self.arc.set_style_arc_width(12, lv.PART.MAIN) #外框宽度

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
    def opa_anmi_callback(self, a, v):
        self.arc.set_style_arc_opa(v, lv.PART.MAIN)
    def setBreath(self):
        self.anim = lv.anim_t()
        self.anim.init()
        self.anim.set_var(self.arc)
        self.anim.set_values(lv.OPA._30, lv.OPA.COVER)
        
        self.anim.set_duration(3000)
        self.anim.set_playback_delay(100)
        self.anim.set_playback_duration(300)
        self.anim.set_repeat_delay(500)

        # 从完全透明到完全不透明
        #self.anim.set_time(3000)  
        # 动画持续时间为1000ms (1秒)
        #self.anim.set_playback_time(1000)  
        # 回放动画，使其来回变化
        self.anim.set_repeat_count(lv.ANIM_REPEAT_INFINITE)
        # 无限循环
        self.anim.set_custom_exec_cb(self.opa_anmi_callback)
        self.anim.start()
    def genTitle(self):
        scr = self.screen
        style = self.genStyle()
        self.title_label = lv.label(scr)
        #self.label.set_text_font(self.myfont_en_100, 0)  # set the font
        self.title_label.align(lv.ALIGN.CENTER, 0, -100)
        self.title_label.set_text('Title')
        self.title_label.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN)
    
    def setTitleText(self, title):
        self.title_label.set_text(title)

    def genUnit(self):
        scr = self.screen
        style = self.genStyle()
        self.unit_label = lv.label(scr)
        #self.label.set_text_font(self.myfont_en_100, 0)  # set the font
        self.unit_label.align(lv.ALIGN.CENTER, 110, 0)
        self.unit_label.set_text('unit')
        self.unit_label.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN)

    def setUnitText(self, unit, x):
        self.unit_label.align(lv.ALIGN.CENTER, x, 0)
        self.unit_label.set_text(unit)

    def genSpeedNum(self):
        scr = self.screen
        style = self.genStyle()
        self.label = lv.label(scr)
        
        self.label.set_style_text_font(self.myfont_en_100, 0)  # set the font
        self.label.align(lv.ALIGN.CENTER, -20, 0)
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

    def on_show(self, v, init=False):            
        scr = self.screen
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
                #self.setColorWheelColor(0x00a5ff)
                '''
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
                '''
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

    def event_handler(self, event):
        code = event.get_code()
        obj = event.get_target()
        if code == lv.EVENT.CLICKED:
            self.cmd.last_cmd_type = self.cmd.cmd_type
            self.cmd.cmd_type = (self.cmd.cmd_type + 1) % len(self.cmd.cmd_map)
            self.on_show(None, True)

    def genFps(self):
        scr = self.screen
        style = self.genStyle()
        self.fps = lv.label(scr)
        #self.label.set_text_font(self.myfont_en_100, 0)  # set the font
        self.fps.align(lv.ALIGN.CENTER, 0, 150)
        self.fps.set_text('fps')
        self.fps.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN)
        
        self.last_time = lv.tick_get()
        self.frame_count = 0
        
        timer = lv.timer_create(self.update_fps, 1000, None)
    # 定义一个更新FPS的函数
    def update_fps(self, task):
        current_time = lv.tick_get()
        elapsed = time.ticks_diff(current_time, self.last_time)
        
        if elapsed > 0:
            fps = (self.frame_count * 1000) / elapsed
            self.fps.set_text(f"FPS: {fps}")  # 更新标签显示
            self.frame_count = 0
            self.last_time = current_time
            print(fps)
        
    def show_lottie(self, file_path, w, h, x, y):
        with open(file_path, 'r') as file:
            json_data = file.read()
            json_bytes = json_data.encode('utf-8')
        
        self.lottie = lv.rlottie_create_from_raw(self.screen, w, h, json_bytes)
        self.lottie.align(lv.ALIGN.CENTER, x, y)
        
def Run():
    screen = Screen()
    resp = {"pid": '0D', 'value': 100}
    #resp = {"pid": '0C', 'value': 1580}

    # 创建定时器更新显示

    while True:
        screen.on_show(resp)
        lv.timer_handler_run_in_period(5)
        #time.sleep(0.005)
        resp['value'] += 1
        screen.frame_count += 1
if __name__ == '__main__':
    Run()

