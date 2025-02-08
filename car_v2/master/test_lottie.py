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

wrapper = lvgl_esp32.Wrapper(display,touch,use_spiram=False, buf_lines=24)
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
        
        with open(file_path, 'r') as file:
            json_data = file.read()
        json_bytes = json_data.encode('utf-8')
        
        #json_bytes = lv_example_rlottie_approve
        lottie = lv.rlottie_create_from_raw(obj, w, h, json_bytes)
        lottie.align(lv.ALIGN.CENTER, x, y)
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
def test_lottie():
    print(wrapper.get_dma_size())
    lottie = show_lottie(screen, "/rlottie/loading.json",200,200,0,0)
    print(wrapper.get_dma_size())
    lottie.delete()
    print(wrapper.get_dma_size())
    del(lottie)
    time.sleep(2)
while True:
    #print("while test")
    lv.timer_handler_run_in_period(5)
    test_lottie()
    #test_ble()
    #test_all()
    #time.sleep(0.005)






