
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
import cmd

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
    
    pidCmd = cmd.Cmd()
    def send_cmd(task):
        for k in pidCmd.cmd_map:
            ret = bo.send(pidCmd.cmd_map[k]["cmd"])
            if not ret:
                scr.set_text("connect")
    

    # 创建定时器更新显示
    timer = lv.timer_create(send_cmd, 200, None)

    #收到消息
    def on_value(v):
        en.Send(bcast, v, False)
        es.append(v)

    def mock_recv(task):
        data_stream = [
            b'410D1E\r\n>',  # 车辆速度
            b'41 0C 0C 35\r\n',  # 引擎转速
            b'41 0D 2A\r\n'  # 车辆速度
            b'14.3V\r\n' #电压
            b'41055A\r\n' #水温
            b'415C6A\r\n' #油温
        ]
        for data in data_stream:
            on_value(data)
    
    #timer = lv.timer_create(mock_recv, 1000, None)

    
    bo = BleObd(on_value)
    while True:
        lv.timer_handler_run_in_period(5)
        bo.run()
        #time.sleep_ms(5)

if __name__ == '__main__':
    Run()
