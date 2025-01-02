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

wrapper = lvgl_esp32.Wrapper(display,touch,use_spiram=True, buf_lines=48)
#wrapper = lvgl_esp32.Wrapper(display,touch,use_spiram=True, buf_lines=48)
wrapper.init()
os.listdir('/sd')
display.brightness(100)
#顺时转180度
display.swapXY(False)
display.mirrorX(True)
display.mirrorY(True)
touch.swapXY(False)
touch.mirrorX(True)
touch.mirrorY(True)

print(wrapper.get_dma_size())

screen = lv.screen_active()
#screen.set_style_bg_color(lv.color_hex(0x000000), lv.PART.MAIN | lv.STATE.DEFAULT)
#screen.set_style_bg_opa(255, lv.PART.MAIN | lv.STATE.DEFAULT)

screen.set_style_bg_color(lv.color_hex(0x202020), lv.PART.MAIN | lv.STATE.DEFAULT)

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

        lottie = lv.rlottie_create_from_raw(obj, w, h, json_bytes)
        lottie.align(lv.ALIGN.CENTER, x, y)
        print(lottie)
        return lottie
        
    except Exception as e:
        print(f"Error creating lottie animation: {e}")
        return None
print(wrapper.get_dma_size())



#show_lottie(screen, "/rlottie/loading.json",150,150,0,0)

print(wrapper.get_dma_size())

print("Memory before:", gc.mem_free())


def test_espnow():
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

while True:
    test_espnow()
    time.sleep(5)
    #lv.timer_handler_run_in_period(5)





