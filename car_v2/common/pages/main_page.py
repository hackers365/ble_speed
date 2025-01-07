import lvgl as lv
import uasyncio as asyncio
from collections import deque
from ble_obd import BleObd
import elm_stream
import cmd
import time
import esp_now
from .base_page import BasePage
import bluetooth
from common.config import Config

class MainPage(BasePage):
    def __init__(self, baseScreen):
        super().__init__(baseScreen)
        self.script_path = baseScreen.script_path
        self.myfont_en_100 = baseScreen.myfont_en_100
        self.bo = None
        self.data_manager = None
        self.es = None
        self.en = None
        self.pidCmd = None
        self.tasks = []
        self.bcast = b'\xff\xff\xff\xff\xff\xff'  # 广播地址
        self.config = baseScreen.get_config()  # Get config from base screen

    def init(self):
        """初始化页面"""
        self._running = True  # 添加运行状态标志
        # 初始化UI组件
        self.genColorWheel()
        self.genSpeedNum()
        self.genTitle()
        self.genUnit()
        # 初始化业务组件
        self.init_components()
        self.init_event()
        # 启动异步任务
        self.start_tasks()
    def init_event(self):
        # 添加点击事件
        self.arc.add_event_cb(self.on_screen_click, lv.EVENT.CLICKED, None)
    def deinit_event(self):
        # 移除点击事件
        #self.screen.remove_event_cb(self.on_screen_click)
        self.arc.remove_event_cb(self.on_screen_click)
    def init_components(self):
        """初始化数据管理和蓝牙组件"""
        # 初始化数据管理器
        self.data_manager = DataManager()
        # 初始化数据解析器
        self.es = elm_stream.ELM327Stream()
        # 初始化指令管理器
        self.pidCmd = cmd.Cmd()
        self.get_dma_size()

        
        # 初始化 ESP-NOW
        def esp_now_recv(mac, msg):
            pass  # 主机模式不需要处理接收
        self.en = esp_now.EspN(esp_now_recv)
        self.en.Run()
        self.en.AddPeer(self.bcast)
        

        # 初始化蓝牙
        def on_value(v):
            if self.data_manager:
                self.data_manager.put_pre_parse_data(v)
                self.data_manager.put_broadcast_data(v)

        # 从配置文件读取蓝牙参数
        ble_config = self.config.get_bluetooth_config()
        ble_params = {'on_value': on_value}

        # 检查必要的蓝牙参数是否同时存在且有值
        if (ble_config.get('uuid') and ble_config.get('rx_char') and 
            ble_config.get('tx_char') and ble_config.get('device_addr')):
            ble_params.update({
                'service_uuid': bluetooth.UUID(ble_config['uuid'].strip("UUID('").strip("')")),
                'rx_char_uuid': bluetooth.UUID(ble_config['rx_char'].strip("UUID('").strip("')")),
                'tx_char_uuid': bluetooth.UUID(ble_config['tx_char'].strip("UUID('").strip("')")),
                'target_addr': ble_config['device_addr']
            })
        print(ble_params)
        self.bo = BleObd(**ble_params)
    
    def genColorWheel(self):
        """生成圆环UI"""
        self.arc = lv.arc(self.screen)
        self.elements.append(self.arc)

        self.arc.set_style_arc_width(12, lv.PART.MAIN)
        self.arc.set_style_bg_opa(lv.OPA.TRANSP, lv.PART.KNOB)
        self.arc.set_style_arc_opa(lv.OPA.TRANSP, lv.PART.INDICATOR)
        self.setColorWheelColor(0x00a5ff)
        
        self.arc.set_bg_angles(0, 360)
        self.arc.set_value(100)
        self.arc.set_size(350, 350)
        self.arc.center()
        
        #self.arc.remove_flag(lv.obj.FLAG.CLICKABLE)
        self.arc.add_flag(lv.obj.FLAG.EVENT_BUBBLE)  # 允许手势冒泡

        self.arc.remove_flag(lv.obj.FLAG.SCROLLABLE)

    def genSpeedNum(self):
        """生成速度显示"""
        self.speed_label = lv.label(self.screen)
        self.elements.append(self.speed_label)
        self.speed_label.set_style_text_font(self.myfont_en_100, 0)
        self.speed_label.set_text("0")
        self.speed_label.align(lv.ALIGN.CENTER, 0, 0)
        self.speed_label.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN)

    def genTitle(self):
        """生成标题"""
        self.title_label = lv.label(self.screen)
        self.elements.append(self.title_label)
        self.title_label.align(lv.ALIGN.CENTER, 0, -100)
        self.title_label.set_text('Speed')
        self.title_label.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN)

    def genUnit(self):
        """生成单位显示"""
        self.unit_label = lv.label(self.screen)
        self.elements.append(self.unit_label)
        self.unit_label.align(lv.ALIGN.CENTER, 0, 50)
        self.unit_label.set_text('km/h')
        self.unit_label.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN)

    def setColorWheelColor(self, color_code):
        """设置圆环颜色"""
        self.arc.set_style_arc_color(lv.color_hex(color_code), lv.PART.MAIN)

    async def send_data(self, data, delay=None):
        """发送数据到OBD设备"""
        ELM_PROMPT = b'>'
        ret = self.bo.send(data)
        if not ret:
            return False
        '''
        if delay:
            await asyncio.sleep(delay)
        
        ret = await self.read_data(ELM_PROMPT)
        if len(ret) > 0:
            return ret
        '''
        return None
        
    async def read_data(self, end_marker=b'>', timeout=1000):
        print("start read_data")
        """读取OBD设备返回的数据"""
        ret = bytearray()
        start_time = time.ticks_ms()
        try:
            while self._running:
                current_time = time.ticks_ms()
                if time.ticks_diff(current_time, start_time) > timeout:
                    return ret

                if not self.data_manager.raw_data_empty():
                    data = self.data_manager.get_raw_data()
                    if data:
                        ret.extend(data)
                        if end_marker in ret:
                            break
            
                await asyncio.sleep_ms(5)
        except Exception as e:
            print('read_data error:', e)
        return ret

    async def collect_data(self):
        """收集数据的协程"""
        while self._running:  # 使用标志控制循环
            try:
                r = self.bo.run()
                if not r:
                    await asyncio.sleep_ms(1000)
                for k in self.pidCmd.cmd_map:
                    if not self._running:  # 检查点
                        return
                    ret = await self.send_data(self.pidCmd.cmd_map[k]["cmd"] + b'\r\n')
                    if ret:
                        self.data_manager.put_pre_parse_data(ret)
                        self.data_manager.put_broadcast_data(ret)
                    await asyncio.sleep_ms(50)
            except Exception as e:
                print('collect_data error:', e)
            await asyncio.sleep_ms(500)  # 主循环检查点
        print("collect data end")

    async def broadcast_data(self):
        """广播数据任务"""
        while self._running:
            #try:
            if not self.data_manager.broadcast_data_empty():
                data = self.data_manager.get_broadcast_data()
                if self.en:
                    self.en.Send(self.bcast, data, False)
            #except Exception as e:
            #    print('broadcast_data error:', e)
            await asyncio.sleep_ms(10)
        print("broadcast_data end")
    async def parse_data(self):
        """解析数据的协程"""
        while self._running:  # 使用标志控制循环
            try:
                if not self.data_manager.pre_parse_empty():
                    raw_data = self.data_manager.get_pre_parse_data()
                    parsed_lists = self.es.append(raw_data)
                    for parsed_data in parsed_lists:
                        if not self._running:  # 检查点
                            return
                        self.data_manager.put_parsed_data(parsed_data)
            except Exception as e:
                print('parse_data error:', e)
            await asyncio.sleep_ms(10)
        print("parse_data end")

    async def display_data(self):
        """显示数据的协程"""
        while self._running:  # 使用标志控制循环
            try:
                if not self.data_manager.parsed_data_empty():
                    data = self.data_manager.get_parsed_data()
                    self.on_show(data)
            except Exception as e:
                print('display_data error:', e)
            #lv.timer_handler_run_in_period(5)
            await asyncio.sleep_ms(5)
        print("display_data end")

    def on_show(self, v, init=False):
        """更新显示数据"""
        try:
            scr = self.screen
            config_info = self.pidCmd.cmd_map[self.pidCmd.cmd_type]
            if init:
                v = config_info
                v["value"] = v["default"]
            same_cmd_type = self.pidCmd.same_cmd_type()
            if "pid" in v:
                if config_info["pid"] == v["pid"]:
                    if not same_cmd_type and 'title' in config_info:
                        self.setTitleText(config_info["title"])
                    #self.setColorWheelColor(0x00a5ff)
                    '''
                    if v["pid"] == '0D':
                        if type(v['value']) != int:
                            print("speed is not int")
                            return
                        if v['value'] <= 40:
                            self.setColorWheelColor(0x90EE90)
                        elif v['value'] <= 60:
                            self.setColorWheelColor(0x00D7FF)
                        elif v['value'] <= 80:
                            self.setColorWheelColor(0xFFBF00)
                        elif v['value'] <= 120:
                            self.setColorWheelColor(0x0045FF)
                        else:
                            self.setColorWheelColor(0x0000FF)
                    else:
                        self.setColorWheelColor(0x00a5ff)
                    '''
                    mainValue = str(v['value'])
                    if not same_cmd_type:
                        unit = ""
                        x = 120
                        if 'unit' in config_info:
                            unit = config_info["unit"]
                        self.setUnitText(unit, x)
                    self.set_text(str(v['value']))
                    self.pidCmd.last_cmd_type = self.pidCmd.cmd_type
        except Exception as e:
            print('on_show error:', e)
    def start_tasks(self):
        """启动所有异步任务"""
        self.tasks = [
            asyncio.create_task(self.collect_data()),
            asyncio.create_task(self.parse_data()),
            asyncio.create_task(self.display_data()),
            asyncio.create_task(self.broadcast_data()),
        ]

    async def _cancel_tasks(self):
        """取消所有任务并等待它们完成"""
        if not self.tasks:
            return
            
        # 取消所有任务
        for task in self.tasks:
            if task and not task.done():
                task.cancel()
        
        # 等待所有任务完成
        for task in self.tasks:
            try:
                await task
            except asyncio.CancelledError:
                pass  # 忽略取消异常
            except Exception as e:
                print(f"Task cancel error: {e}")
                
        # 清理任务列表
        self.tasks.clear()

    def destroy(self):
        """页面销毁时清理资源"""
        #try:
            # 设置停止标志
        self._running = False
        
        # 创建并运行取消任务
        #asyncio.run(self._cancel_tasks())
        asyncio.gather(*self.tasks)
        print("after gather")
        # 清理蓝牙连接
        if self.bo:
            self.bo.destroy()
            self.bo = None
            
        # 最后清理对象引用
        self.data_manager = None
        self.es = None
        self.pidCmd = None

        #清理espnow
        
        if self.en:
            self.en.destroy()
            self.en = None
        self.deinit_event()

        # 调用父类的 destroy
        super().destroy()
        '''
        except Exception as e:
            print(f"Destroy error: {e}")
        '''
    def setTitleText(self, text):
        """设置标题文本"""
        try:
            if hasattr(self, 'title_label'):
                self.title_label.set_text(text)
        except Exception as e:
            print('setTitleText error:', e)

    def setUnitText(self, text, x_offset=110):
        """设置单位文本"""
        try:
            if hasattr(self, 'unit_label'):
                self.unit_label.set_text(text)
                # 根据主值的长度调整单位标签的位置
                self.unit_label.align(lv.ALIGN.CENTER, x_offset, 0)
        except Exception as e:
            print('setUnitText error:', e)

    def set_text(self, text):
        """设置主显示文本"""
        try:
            if hasattr(self, 'speed_label'):
                self.speed_label.set_text(str(text))
        except Exception as e:
            print('set_text error:', e)

    def on_screen_click(self, event):
        """处理屏幕点击事件"""
        try:
            if not self.pidCmd or not self.pidCmd.cmd_map:
                return
            print("on_screen_click")
            # 切换到下一个PID
            self.pidCmd.cmd_type = (self.pidCmd.cmd_type + 1) % len(self.pidCmd.cmd_map)
            self.on_show(None, True)
            
        except Exception as e:
            print('on_screen_click error:', e)

class DataManager:
    """数据管理器类"""
    def __init__(self):
        self.raw_data_queue = deque((), 20)       # 原始数据队列
        self.pre_parse_queue = deque((), 20)      # 预解析数据队列
        self.parsed_data_queue = deque((), 20)    # 解析后的数据队列
        self.broadcast_queue = deque((), 20)    # 广播数据队列
    
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
    
    def raw_data_empty(self):
        return len(self.raw_data_queue) == 0
    
    def pre_parse_empty(self):
        return len(self.pre_parse_queue) == 0
    
    def parsed_data_empty(self):
        return len(self.parsed_data_queue) == 0
    
    def put_broadcast_data(self, data):
        self.broadcast_queue.append(data)

    def get_broadcast_data(self):
        return self.broadcast_queue.popleft() if self.broadcast_queue else None

    def broadcast_data_empty(self):
        return len(self.broadcast_queue) == 0