import lvgl as lv
import uasyncio as asyncio
from collections import deque
from ble_obd import BleObd
import elm_stream
import cmd
import time
from .base_page import BasePage

class MainPage(BasePage):
    def __init__(self, baseScreen):
        super().__init__(baseScreen)
        self.script_path = baseScreen.script_path
        self.myfont_en_100 = baseScreen.myfont_en_100
        self.bo = None
        self.data_manager = None
        self.es = None
        self.pidCmd = None
        self.tasks = []
        self._running = True  # 添加运行状态标志
        
    def init(self):
        """初始化页面"""
        # 初始化UI组件
        self.genColorWheel()
        self.genSpeedNum()
        self.genTitle()
        self.genUnit()
        # 初始化业务组件
        self.init_components()
        # 启动异步任务
        self.start_tasks()

    def init_components(self):
        """初始化数据管理和蓝牙组件"""
        # 初始化数据管理器
        self.data_manager = DataManager()
        # 初始化数据解析器
        self.es = elm_stream.ELM327Stream()
        # 初始化指令管理器
        self.pidCmd = cmd.Cmd()
        # 初始化蓝牙
        def on_value(v):
            self.data_manager.put_raw_data(v)
        self.bo = BleObd(on_value)

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
        
        self.arc.remove_flag(lv.obj.FLAG.CLICKABLE)
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
        if delay:
            await asyncio.sleep(delay)
        
        ret = await self.read_data(ELM_PROMPT)
        if len(ret) > 0:
            return ret
        return None

    async def read_data(self, end_marker=b'>', timeout=1000):
        """读取OBD设备返回的数据"""
        ret = bytearray()
        start_time = time.ticks_ms()
        try:
            while True:
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
                self.bo.run()
                for k in self.pidCmd.cmd_map:
                    if not self._running:  # 检查点
                        return
                    ret = await self.send_data(self.pidCmd.cmd_map[k]["cmd"] + b'\r\n')
                    if ret:
                        self.data_manager.put_pre_parse_data(ret)
                    await asyncio.sleep_ms(10)
            except Exception as e:
                print('collect_data error:', e)
            await asyncio.sleep_ms(5)  # 主循环检查点

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

    async def display_data(self):
        """显示数据的协程"""
        while self._running:  # 使用标志控制循环
            try:
                if not self.data_manager.parsed_data_empty():
                    data = self.data_manager.get_parsed_data()
                    self.on_show(data)
            except Exception as e:
                print('display_data error:', e)
            lv.timer_handler_run_in_period(5)
            await asyncio.sleep_ms(5)

    def on_show(self, data):
        """更新显示数据"""
        try:
            if "SPEED" in data:
                speed = data["SPEED"]
                self.speed_label.set_text(str(speed))
                # 更新圆环颜色
                if speed < 60:
                    self.setColorWheelColor(0x00a5ff)
                elif speed < 120:
                    self.setColorWheelColor(0x00ff00)
                else:
                    self.setColorWheelColor(0xff0000)
        except Exception as e:
            print('on_show error:', e)

    def start_tasks(self):
        """启动所有异步任务"""
        self.tasks = [
            asyncio.create_task(self.collect_data()),
            asyncio.create_task(self.parse_data()),
            asyncio.create_task(self.display_data())
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
        try:
            await asyncio.gather(*self.tasks, return_exceptions=True)
        except asyncio.CancelledError:
            pass  # 忽略取消异常
        except Exception as e:
            print(f"Task cancel error: {e}")
        finally:
            self.tasks.clear()

    def destroy(self):
        """页面销毁时清理资源"""
        try:
            # 设置停止标志
            self._running = False
            
            # 创建并运行取消任务
            asyncio.create_task(self._cancel_tasks())
            
            # 清理蓝牙连接
            if self.bo:
                self.bo.destroy()
                self.bo = None
                
            # 最后清理对象引用
            self.data_manager = None
            self.es = None
            self.pidCmd = None
            
            # 调用父类的 destroy
            super().destroy()
        except Exception as e:
            print(f"Destroy error: {e}")

class DataManager:
    """数据管理器类"""
    def __init__(self):
        self.raw_data_queue = deque((), 20)       # 原始数据队列
        self.pre_parse_queue = deque((), 20)      # 预解析数据队列
        self.parsed_data_queue = deque((), 20)    # 解析后的数据队列
    
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