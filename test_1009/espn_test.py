import network
import espnow

import time
#import ble_obd_test as ble_obd

import bluetooth

import micropython
import gc
import machine



from hardware import display,touch
import lvgl as lv
import lvgl_esp32
#from ble_uart_peripheral import demo

def init_screen():
    wrapper = lvgl_esp32.Wrapper(display, touch)
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


def init_espnow():
    # A WLAN interface must be active to send()/recv()
    sta = network.WLAN(network.STA_IF)  # Or network.AP_IF
    sta.active(True)
    sta.disconnect()      # For ESP8266

    e = espnow.ESPNow()
    e.active(True)

    #peer = b'\xbb\xbb\xbb\xbb\xbb\xbb'   # MAC address of peer's wifi interface
    #e.add_peer(peer)      # Must add_peer() before send()

    peer = b'\xff\xff\xff\xff\xff\xff'
    e.add_peer(peer)      # Must add_peer() before send()

def init_ble():
    ble = bluetooth.BLE()
    ble.active(True)

def mem():
    micropython.mem_info()
    #micropython.qstr_info()
    #gc.collect()
    print(gc.mem_free())

mem()
init_screen()
#init_ble()
mem()
#init_espnow()
mem()



