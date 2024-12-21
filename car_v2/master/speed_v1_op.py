import usys as sys
sys.path.append('/common')
import micropython, gc
import uasyncio as asyncio
from collections import deque
from ble_obd import BleObd
import elm_stream
import lvgl as lv
import esp_now
import screen
import cmd
import time

ELM_PROMPT = b'>'

class DataManager:
    def __init__(self):
        self.raw_data_queue = deque((), 20)       # 原始数据队列
        self.pre_parse_queue = deque((), 20)      # 预解析数据队列
        self.parsed_data_queue = deque((), 20)    # 解析后的数据队列
        self.broadcast_queue = deque((), 20)      # 待广播数据队列
    
    def put_raw_data(self, data):
        self.raw_data_queue.append(data)
    
    def get_raw_data(self):
        return self.raw_data_queue.popleft() if self.raw_data_queue else None
    
    def put_pre_parse_data(self, data):
        self.pre_parse_queue.append(data)
    
    def get_pre_parse_data(self):
        return self.pre_parse_queue.popleft() if self.pre_parse_queue else None
    
    def put_parsed_data(self, data):
        self.parsed_data_queue.append(data)
    
    def get_parsed_data(self):
        return self.parsed_data_queue.popleft() if self.parsed_data_queue else None
    
    def put_broadcast_data(self, data):
        self.broadcast_queue.append(data)
    
    def get_broadcast_data(self):
        return self.broadcast_queue.popleft() if self.broadcast_queue else None
    
    def raw_data_empty(self):
        return len(self.raw_data_queue) == 0
    
    def pre_parse_empty(self):
        return len(self.pre_parse_queue) == 0
    
    def parsed_data_empty(self):
        return len(self.parsed_data_queue) == 0
    
    def broadcast_data_empty(self):
        return len(self.broadcast_queue) == 0

async def send_data(bo, data, data_manager, delay=None, end_marker=ELM_PROMPT):
    ret = bo.send(data)
    if not ret:
        return False
    delayed = 0
    if delay is not None:
        await asyncio.sleep(delay)
        delayed += delay
    
    r = await read_data(bo, data_manager, end_marker)
    if len(r) > 0:
        return r
    return None

async def read_data(bo, data_manager, end_marker=ELM_PROMPT, timeout=None):
    ret = bytearray()
    start_time = time.ticks_ms()
    if timeout is None:
        timeout = 1000

    while True:
        current_time = time.ticks_ms()
        if time.ticks_diff(current_time, start_time) > timeout:
            return False
            
        if not data_manager.raw_data_empty():
            data = data_manager.get_raw_data()
            if data:
                ret.extend(data)
                if end_marker in ret:
                    break
        
        await asyncio.sleep_ms(5)
    
    return ret

async def collect_data(bo, pidCmd, data_manager):
    while True:
        try:
            bo.run()
            for k in pidCmd.cmd_map:
                ret = await send_data(bo, pidCmd.cmd_map[k]["cmd"] + b'\r\n', data_manager)
                if ret:
                    data_manager.put_pre_parse_data(ret)
                    data_manager.put_broadcast_data(ret)
                await asyncio.sleep_ms(10)
        except Exception as e:
            print('collect_data error:', e)

async def broadcast_data(en, bcast, data_manager):
    """广播数据任务"""
    while True:
        try:
            if not data_manager.broadcast_data_empty():
                data = data_manager.get_broadcast_data()
                en.Send(bcast, data, False)
        except Exception as e:
            print('broadcast_data error:', e)
        await asyncio.sleep_ms(10)

async def parse_data(data_manager, es):
    while True:
        try:
            if not data_manager.pre_parse_empty():
                raw_data = data_manager.get_pre_parse_data()
                parsed_lists = es.append(raw_data)
                for parsed_data in parsed_lists:
                    data_manager.put_parsed_data(parsed_data)
        except Exception as e:
            print('parse_data error:', e)
        await asyncio.sleep_ms(10)

async def display_data(data_manager, scr):
    """显示数据任务"""
    while True:
        try:
            if not data_manager.parsed_data_empty():
                data = data_manager.get_parsed_data()
                # 更新屏幕显示
                scr.on_show(data)  # 假设Screen类有show方法来显示数据
        except Exception as e:
            print('display_data error:', e)
        lv.timer_handler_run_in_period(5)
        await asyncio.sleep_ms(5)

async def iRun():
    # 初始化 ESP-NOW
    def esp_now_recv(mac, msg):
        pass
    en = esp_now.EspN(esp_now_recv)
    en.Run()
    bcast = b'\xff\xff\xff\xff\xff\xff'
    en.AddPeer(bcast)

    #初始化屏幕
    scr = screen.Screen()  # 初始化屏幕

    # 初始化其他组件
    es = elm_stream.ELM327Stream()  # 简化回调
    pidCmd = cmd.Cmd()
    data_manager = DataManager()
    
    def on_value(v):
        data_manager.put_raw_data(v)
    
    bo = BleObd(on_value)

    lv.timer_handler_run_in_period(5)
    # 创建并运行所有任务
    tasks = [
        asyncio.create_task(collect_data(bo, pidCmd, data_manager)),
        asyncio.create_task(broadcast_data(en, bcast, data_manager)),
        asyncio.create_task(parse_data(data_manager, es)),
        asyncio.create_task(display_data(data_manager, scr))
    ]

    # 等待所有任务完成（实际上是无限循环）
    await asyncio.gather(*tasks)

def Run():
    asyncio.run(iRun())

if __name__ == '__main__':
    Run()


