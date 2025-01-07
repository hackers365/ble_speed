import usys as sys
sys.path.append('/common') # See: https://github.com/micropython/micropython/issues/6419
sys.path.append('/rlottie') # See: https://github.com/micropython/micropython/issues/6419

from hardware import display,touch

import fs_driver

import lvgl as lv
import lvgl_esp32
import os
import time
import esp_now
import gc
import esp_now
from ble_obd import BleScan

wrapper = lvgl_esp32.Wrapper(display,touch,use_spiram=False, buf_lines=48)
#wrapper = lvgl_esp32.Wrapper(display,touch,use_spiram=True, buf_lines=48)
wrapper.init()
os.listdir('/sd')
display.brightness(60)
#顺时转180度
display.swapXY(False)
display.mirrorX(True)
display.mirrorY(True)
touch.swapXY(False)
touch.mirrorX(True)
touch.mirrorY(True)

print(wrapper.get_dma_size())

screen = lv.screen_active()
screen.set_style_bg_color(lv.color_hex(0x000000), lv.PART.MAIN | lv.STATE.DEFAULT)
screen.set_style_bg_opa(255, lv.PART.MAIN | lv.STATE.DEFAULT)
label = lv.label(screen)
label.set_text(f"MicroPython{os.uname()[2]}")
label.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN)
label.align(lv.ALIGN.CENTER, 0, 0)

def show_lottie(obj, file_path, w, h, x, y):
    """
    显示 lottie 动画
    :param file_path: json 文件路径
    :param w: 宽度
    :param h: 高度
    :param x: x 偏移
    :param y: y 偏移
    :return: lottie 动画对象
    """
    try:
        print("before load file:", wrapper.get_dma_size())
        with open(file_path, 'r') as file:
            json_data = file.read()
        file.close()
        json_bytes = json_data.encode('utf-8')
        print("after load file:", wrapper.get_dma_size())
        
        #json_bytes = lv_example_rlottie_approve
        lottie = lv.rlottie_create_from_raw(obj, w, h, json_bytes)
        lottie.align(lv.ALIGN.CENTER, x, y)
        
        del json_bytes
        return lottie
        
    except Exception as e:
        print(f"Error creating lottie animation: {e}")
        return None


print("Memory before:", gc.mem_free())

def test_ble():
    print(wrapper.get_dma_size())
    ble_scanner = BleScan()
    ble_scanner.start_scan(callback=None, duration_ms=5000, completion_callback=None)
    print(wrapper.get_dma_size())
    time.sleep(10)
    
    ble_scanner.destroy()
    print(wrapper.get_dma_size())

def test_espnow():
    print(wrapper.get_dma_size())
    #init esp now broadcast
    def esp_now_recv(mac, msg):
        pass
    en = esp_now.EspN(esp_now_recv)
    en.Run()
    bcast = b'\xff\xff\xff\xff\xff\xff'
    en.AddPeer(bcast)

    print("启动")

    print(wrapper.get_dma_size())

    en.destroy()
    print(wrapper.get_dma_size())

    gc.collect()
    print("Memory after:", gc.mem_free())

def test_all():
    print("start:", wrapper.get_dma_size())
    ble_scanner = BleScan()
    ble_scanner.start_scan(callback=None, duration_ms=5000, completion_callback=None)
    
    print("after ble start:", wrapper.get_dma_size())
    def esp_now_recv(mac, msg):
        pass
    en = esp_now.EspN(esp_now_recv)
    en.Run()
    bcast = b'\xff\xff\xff\xff\xff\xff'
    en.AddPeer(bcast)
    print("after ble and espnow start:", wrapper.get_dma_size())
    
    time.sleep(5)
    ble_scanner.destroy()
    print("after ble destroy:", wrapper.get_dma_size())
    en.destroy()
    print("after espnow destroy:",wrapper.get_dma_size())
    
#test_ble()
#test_espnow()
def test_lottie(file_path):
    print(wrapper.get_dma_size())
    lottie = show_lottie(screen, file_path,150,150,0,0)
    time.sleep(3)
    lottie.delete()
    del lottie
    gc.collect()
    print(wrapper.get_dma_size())

def show_msgbox(msg, title=None, timeout=2000):
    """
    显示消息框
    :param title: 标题
    :param msg: 消息内容
    :param timeout: 自动关闭时间(毫秒)，默认2秒
    """
    mbox = lv.msgbox(screen)
    
    # 设置标题和内容
    if title:
        mbox.add_title(title)
    mbox.add_text(msg)
    
    # 设置整体样式
    mbox.set_style_bg_color(lv.color_hex(0xFFFFFF), lv.PART.MAIN)  # 白色背景
    mbox.set_style_border_color(lv.color_hex(0xE0E0E0), lv.PART.MAIN)  # 浅灰色边框
    mbox.set_style_border_width(2, lv.PART.MAIN)
    mbox.set_style_radius(10, lv.PART.MAIN)
    mbox.set_style_shadow_width(20, lv.PART.MAIN)
    mbox.set_style_shadow_color(lv.color_hex(0x000000), lv.PART.MAIN)
    mbox.set_style_shadow_opa(30, lv.PART.MAIN)  # 降低阴影透明度
    mbox.set_style_pad_all(20, lv.PART.MAIN)
    
    # 设置文字样式
    mbox.set_style_text_color(lv.color_hex(0x333333), lv.PART.MAIN)  # 深灰色文字
    mbox.set_style_text_font(lv.font_montserrat_20, lv.PART.MAIN)
    mbox.set_style_text_align(lv.TEXT_ALIGN.CENTER, lv.PART.MAIN)
    
    # 如果有标题，设置标题样式
    '''
    if title:
        mbox.set_style_text_font(lv.font_montserrat_20, lv.PART.TITLE)
        mbox.set_style_pad_bottom(15, lv.PART.TITLE)
        mbox.set_style_text_align(lv.TEXT_ALIGN.CENTER, lv.PART.TITLE)
        mbox.set_style_text_color(lv.color_hex(0x222222), lv.PART.TITLE)  # 标题文字颜色
    '''

    # 调整内容区域样式
    mbox.set_style_pad_ver(20, lv.PART.MAIN)
    mbox.set_style_pad_hor(30, lv.PART.MAIN)
    
    mbox.center()
    
    # 设置定时器自动关闭
    timer = lv.timer_create(lambda t: mbox.delete(), timeout, None)
    timer.set_repeat_count(1)

show_msgbox("提示", "正在加载动画...")
while True:
    #print("while test")
    lv.timer_handler_run_in_period(5)
    time.sleep(0.01)



