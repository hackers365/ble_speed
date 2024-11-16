
import usys as sys
sys.path.append('') # See: https://github.com/micropython/micropython/issues/6419

import micropython,gc

import time
# Initialize
from ble_obd import BleObd

import lvgl as lv
import elm_stream
import esp_now
import screen

cmd_map = {
    0: {"cmd": b"010C\r\n", "pid": bytearray(b'0C')},
    1: {"cmd": b"010D\r\n", "pid": bytearray(b'0D')},
    2: {"cmd": b"ATRV\r\n", "pid": bytearray(b'RV')}
}
cmd_type = 1

def Run():
    #init esp now broadcast
    def esp_now_recv(mac, msg):
        pass
    en = esp_now.EspN(esp_now_recv)
    en.Run()
    bcast = b'\xff\xff\xff\xff\xff\xff'
    en.AddPeer(bcast)

    scr = screen.Screen()

    es = elm_stream.ELM327Stream(scr.on_show)

    def send_cmd(task):
        for k in cmd_map:
            time.sleep(0.1)
            ret = bo.send(cmd_map[k]["cmd"])
            if not ret:
                scr.set_text("connect")
        
    # 创建定时器更新显示
    timer = lv.timer_create(send_cmd, 200, None)

    #收到消息
    def on_value(v):
        en.Send(bcast, v, False)
        es.append(v)

    bo = BleObd(on_value)
    while True:
        lv.timer_handler_run_in_period(5)
        bo.run()
        time.sleep_ms(5)

if __name__ == '__main__':
    Run()
