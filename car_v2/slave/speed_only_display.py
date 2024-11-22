
import usys as sys
sys.path.append('') # See: https://github.com/micropython/micropython/issues/6419

import micropython,gc

import time
# Initialize

import lvgl as lv
import elm_stream
import esp_now
import screen


def Run():
    scr = screen.Screen()
    es = elm_stream.ELM327Stream(scr.on_show)

    #init esp now broadcast
    def esp_now_recv(mac, msg):
        es.append(v)
    en = esp_now.EspN(esp_now_recv)
    en.Run()
    bcast = b'\xff\xff\xff\xff\xff\xff'
    en.AddPeer(bcast)

    while True:
        lv.timer_handler_run_in_period(5)

if __name__ == '__main__':
    Run()

