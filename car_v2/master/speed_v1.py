
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

import uasyncio as asyncio

def genCmdBytes(cmd_map):
    cmd_bytes = bytearray(b'01')
    for k in cmd_map:
        if "skip_multi" in k:
            continue
        cmd_bytes.extend(cmd_map[k]["pid"])
    cmd_bytes.extend(b'\r\n')
    return cmd_bytes

def genInitCmd():
    cmd_bytes = bytearray()
    return [b'ATE0\r\n', b'ATL0\r\n', b'ATS0\r\n']

bol_init_cmd = False

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
        global bol_init_cmd
        if not bol_init_cmd:
            for init_cmd in genInitCmd():
                ret = bo.send(init_cmd)
                if not ret:
                    return
                time.sleep(1)
            bol_init_cmd = True
        
        ret = bo.send(cmd_bytes)
        if not ret:
            scr.set_text("init")
            return

        '''
        for k in pidCmd.cmd_map:
            ret = bo.send(pidCmd.cmd_map[k]["cmd"])
            if not ret:
                scr.set_text("init")
                return
            time.sleep_ms(200)
        '''
          
    # 创建定时器更新显示
    timer = lv.timer_create(send_cmd, 500, None)

    #收到消息
    def on_value(v):
        en.Send(bcast, v, False)
        es.append(v)

    bo = BleObd(on_value)
    while True:
        lv.timer_handler_run_in_period(5)
        bo.run()
        #time.sleep_ms(5)

if __name__ == '__main__':
    Run()
