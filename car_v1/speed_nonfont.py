
import usys as sys
sys.path.append('') # See: https://github.com/micropython/micropython/issues/6419

import micropython,gc

import time
# Initialize
from hardware import display,touch
from ble_obd import BleObd

import lvgl as lv
import lvgl_esp32

import elm_stream
import esp_now

#import fs_driver


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
screen = lv.screen_active()
screen.set_style_bg_color(lv.color_hex(0x000000), lv.PART.MAIN | lv.STATE.DEFAULT)
screen.set_style_bg_opa(255, lv.PART.MAIN | lv.STATE.DEFAULT)

#init font
'''
try:
    script_path = __file__[:__file__.rfind('/')] if __file__.find('/') >= 0 else '.'
except NameError:
    script_path = ''

fs_drv = lv.fs_drv_t()
fs_driver.fs_register(fs_drv, 'S')

#myfont_en_150 = lv.binfont_create("S:%s/font/speed_num_consolas_150.bin" % script_path)
myfont_en_100 = lv.binfont_create("S:%s/font/speed_num_consolas_100.bin" % script_path)
'''

class Speed():
    def __init__(self, scr):
        self.genColorWheel(scr)
        self.genSpeedNum(scr)
    def genColorWheel(self, scr):
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
        self.arc.add_event_cb(event_handler, lv.EVENT.CLICKED, None)
    def setColorWheelColor(self, color_code):  #不是rgv, 是bgr
        self.arc.set_style_arc_color(lv.color_hex(color_code), lv.PART.MAIN)
    
    def genSpeedNum(self, scr):
        style = self.genStyle()
        self.label = lv.label(scr)
        #self.label.set_style_text_font(myfont_en_100, 0)  # set the font
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


cmd_map = {
    0: b"010C\r\n",
    1: b"010D\r\n",
    2: b"ATRV\r\n"
}
cmd_type = 1

def event_handler(event):
    code = event.get_code()
    obj = event.get_target()
    global cmd_type
    #print(obj)
    #print(code)
    if code == lv.EVENT.CLICKED:
        cmd_type = (cmd_type + 1) % len(cmd_map)

def mem_info():
    #micropython.mem_info()
    print(gc.mem_alloc())

total_count = 0
pre_count = 0

def Run():
    #screen.add_event_cb(event_handler, lv.EVENT.CLICKED, None)

    #init esp now broadcast
    def esp_now_recv(mac, msg):
        pass
    
    en = esp_now.EspN(esp_now_recv)
    en.Run()

    bcast = b'\xff\xff\xff\xff\xff\xff'
    en.AddPeer(bcast)
    
    #init ble
    scr = Speed(screen)
    
    count = 0
    pre_count = 0
    def on_show(v):
        #print("on_show")
        #print(str(v))
        global total_count
        total_count+=1
        if cmd_type == 1:
            if type(v['value']) != int:
                print("speed is not int")
                return
            if v['value'] <= 40:
                scr.setColorWheelColor(0x90EE90)
            elif v['value'] <= 60:
                scr.setColorWheelColor(0x00D7FF)
            elif v['value'] <= 80:
                scr.setColorWheelColor(0xFFBF00)
            elif v['value'] <= 120:
                scr.setColorWheelColor(0x0045FF)
            else:
                scr.setColorWheelColor(0x0000FF)
        else:
            scr.setColorWheelColor(0x00a5ff)
        scr.set_text(str(v['value']))

    es = elm_stream.ELM327Stream(on_show)

    def send_cmd(task):
        ret = bo.send(cmd_map[cmd_type])
        if not ret:
            scr.set_text("connect")
        #mem_info()
        #except:
        #    print("TX failed")
    def statistics(task):
        global total_count
        global pre_count
        print(total_count-pre_count)
        pre_count = total_count
        
    # 创建定时器更新显示
    timer = lv.timer_create(send_cmd, 1000, None)
    timer = lv.timer_create(statistics, 1000, None)
        #收到消息
    def on_value(v):
        #en.Send(bcast, v, False)
        es.append(v)
    mem_info()
    bo = BleObd(on_value)
    while True:
        lv.timer_handler_run_in_period(5)
        bo.run()

#if __name__ == '__main__':
Run()

