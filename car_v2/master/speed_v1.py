
import usys as sys
sys.path.append('/common') # See: https://github.com/micropython/micropython/issues/6419

import micropython,gc

import time
# Initialize
from ble_obd import BleObd

import lvgl as lv
import elm_stream
import esp_now
import screen
import cmd

def genCmdBytes(cmd_map):
    cmd_bytes = bytearray()
    for k in cmd_map:
        cmd_bytes.extend(cmd_map[k]["cmd"])
        cmd_bytes.extend(b' ')
    cmd_bytes.extend(b'\r\n')
    return cmd_bytes

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
    cmd_bytes = genCmdBytes(pidCmd.cmd_map)
    print(cmd_bytes)
    def send_cmd(task):
        ret = bo.send(cmd_bytes)
        if not ret:
            scr.set_text("init")
    
    # 创建定时器更新显示
    timer = lv.timer_create(send_cmd, 200, None)

    #收到消息
    def on_value(v):
        en.Send(bcast, v, False)
        es.append(v)

    def mock_recv(task):
        data_stream = [
            b'ATRV\r14.5V\r\r>0105\r',  # 车辆速度
            b'41 05 4A \r',  # 引擎转速
            b'\r>',  # 车辆速度
            b'015C\rSTOPPED\r\r>>',  # 车辆速度
            b'010D\r',  # 车辆速度
            b'41 0D 00 \r41 0D 00 \r',  # 车辆速度
            b'\r>ATRV\r14.5V\r\r>',  # 车辆速度
            b'0105\r',  # 车辆速度
            b'41 05 4A \r',
            b'\r>015C\r',
            b'NO DATA\r\r>',
            b'010C\r41 0C 14 28 \r41',
            b' 0C 14 12 \rSTOPPED\r\r',
            b'>',
            b'410C1429>',
            b'410C1430410C1435>',
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
