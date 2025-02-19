import lvgl as lv
import uasyncio as asyncio
from collections import deque
from common.aioble_obd import AioBleObd
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
        self.myfont_en_50 = baseScreen.myfont_en_50
        self.bo = None
        self.data_manager = None
        self.es = None
        self.pidCmd = None
        self.espn = None
        self.tasks = []
        self.bcast = b'\xff\xff\xff\xff\xff\xff'  # 广播地址
        self.config = baseScreen.get_config()  # Get config from base screen
        self.skip_counter = 0  # 添加skip命令计数器
        self.ble_params = None
        self.obd_via_espnow = self.config.get_obd_espnow() if hasattr(self.config, 'get_obd_espnow') else False
        self.door_labels = {}  # 存储车门状态标签
        self.gear_label = None  # 档位标签
        self.blinker_arcs = {'left': None, 'right': None}  # 转向灯弧形
        self.blinker_timer = None  # 闪烁定时器
        self.blinker_state = False  # 闪烁状态
        self.drive_mode_label = None  # 驾驶模式标签

    def init(self):
        """初始化页面"""
        self._running = True  # 添加运行状态标志
        self.run_mode = self.config.get_run_mode()
        print("run_mode:", self.run_mode)
        
        # 初始化UI组件
        self.genColorWheel()
        self.genSpeedNum()
        self.genTitle()
        self.genUnit()
        self.genImage()
        self.genDoorLabels()  # 添加车门状态标签
        self.genGearLabel()   # 添加档位标签
        self.genBlinkerArcs()  # 添加转向灯弧形
        
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
    def is_master(self):
        return self.run_mode == 'master'
    def init_components(self):
        """初始化组件"""
        self.init_common_components()
        if self.is_master():
            self.init_master_components()
        else:
            self.init_slave_components()
    def init_common_components(self):
        """初始化通用组件"""
        # 初始化数据管理器
        self.data_manager = DataManager()
        # 初始化数据解析器
        self.es = elm_stream.ELM327Stream()
        # 初始化指令管理器
        self.pidCmd = cmd.Cmd()
        self.get_dma_size()
    
    def init_master_components(self):
        # 如果启用了OBD ESP-NOW模式，跳过蓝牙初始化
        if self.obd_via_espnow:
            self.init_espnow()
            return

        # 初始化蓝牙
        self.bo = AioBleObd()
        
        # 从配置文件读取蓝牙参数
        ble_config = self.config.get_bluetooth_config()
        
        # 检查必要的蓝牙参数是否同时存在且有值
        if (ble_config.get('uuid') and ble_config.get('rx_char') and 
            ble_config.get('tx_char') and ble_config.get('device_addr')):
            
            def convert_uuid(uuid_val):
                if isinstance(uuid_val, str) and uuid_val.startswith('0x'):
                    # 如果是0x开头的字符串，转换为整数
                    return int(uuid_val, 16)
                return str(uuid_val)  # 其他情况转为字符串
            
            self.ble_params = {
                'service_uuid': convert_uuid(ble_config['uuid']),
                'tx_uuid': convert_uuid(ble_config['tx_char']),
                'rx_uuid': convert_uuid(ble_config['rx_char']),
                'addr': ble_config['device_addr']
            }
            print("BLE params:", self.ble_params)
    def init_slave_components(self):
        """初始化slave组件"""
        self.init_espnow()
    def init_espnow(self):
        """初始化espnow组件"""
        def esp_now_recv(mac, msg):
            self.data_manager.put_pre_parse_data(msg)
        self.espn = esp_now.EspN(esp_now_recv)
        self.espn.Run()
        self.espn.AddPeer(self.bcast)
    def genImage(self):
        """根据配置生成图片"""
        # 检查配置是否允许显示图片
        if not self.config.get_show_image():
            return
            
        with open('%s/car.png' % self.script_path, 'rb') as f:
            png_data = f.read()
        
        png_image_dsc = lv.image_dsc_t({
            'data_size': len(png_data),
            'data': png_data 
        })

        # Create an image using the decoder
        image1 = lv.image(self.screen)
        image1.set_src(png_image_dsc)
        image1.set_pos(100,240)
        
        # 将图片对象添加到elements列表中以便清理
        self.elements.append(image1)

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
        self.speed_label.set_text("")
        self.speed_label.align(lv.ALIGN.CENTER, 0, 25)
        self.speed_label.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN)

    def genTitle(self):
        """生成标题"""
        self.title_label = lv.label(self.screen)
        self.elements.append(self.title_label)
        self.title_label.align(lv.ALIGN.CENTER, 0, -120)
        self.title_label.set_text('Speed')
        self.title_label.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN)

    def genUnit(self):
        """生成单位显示"""
        self.unit_label = lv.label(self.screen)
        self.elements.append(self.unit_label)
        self.unit_label.align(lv.ALIGN.CENTER, 110, 15)
        self.unit_label.set_text('km/h')
        self.unit_label.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN)

    def setColorWheelColor(self, color_code):
        """设置圆环颜色"""
        self.arc.set_style_arc_color(lv.color_hex(color_code), lv.PART.MAIN)

    async def send_obd_command(self, command):
        """
        统一的OBD命令发送方法
        根据obd_via_espnow配置决定使用ESP-NOW还是蓝牙发送
        """
        try:
            if self.obd_via_espnow:
                # ESP-NOW模式
                return self.espn.Send(self.bcast, command, False)
            else:
                # 蓝牙模式
                if self.bo and self.bo.is_connected:
                    return await self.bo.send(command)
                return False
        except Exception as e:
            print(f"send_obd_command error: {e}")
            return False

    async def collect_data(self):
        """收集数据的协程"""
        while self._running:
            try:
                print("obd_via_espnow:", self.obd_via_espnow)
                # 如果是ESP-NOW模式，跳过蓝牙连接检查
                if not self.obd_via_espnow:
                    # 连接设备
                    if not self.bo.is_connected:
                        # 隐藏显示内容
                        self.speed_label.add_flag(lv.obj.FLAG.HIDDEN)
                        self.title_label.add_flag(lv.obj.FLAG.HIDDEN)
                        self.unit_label.add_flag(lv.obj.FLAG.HIDDEN)
                        
                        # 检查是否已经显示loading动画
                        if not hasattr(self, 'loading') or not self.loading:
                            # 显示 loading 动画
                            self.loading = self.show_lottie(self.screen, "/rlottie/loading.json", 150, 150, 0, 0)
                        success = False
                        if self.ble_params:
                            success = await self.bo.connect_to_service(
                                self.ble_params['addr'], 
                                self.ble_params['service_uuid'], 
                                self.ble_params['tx_uuid'], 
                                self.ble_params['rx_uuid']
                            )
                        
                        if success:
                            # 连接成功才删除loading动画
                            if hasattr(self, 'loading') and self.loading:
                                self.loading.delete()
                                self.loading = None
                            # 恢复初始显示
                            self.speed_label.remove_flag(lv.obj.FLAG.HIDDEN)
                            self.title_label.remove_flag(lv.obj.FLAG.HIDDEN)
                            self.unit_label.remove_flag(lv.obj.FLAG.HIDDEN)
                        else:
                            # 连接失败，保持loading动画显示
                            await asyncio.sleep_ms(3000)
                            continue

                # 发送主命令
                if self.obd_via_espnow:
                    for k in self.pidCmd.espnow_cmd_map:
                        if not await self.send_obd_command(self.pidCmd.espnow_cmd_map[k]["cmd"]):
                            await asyncio.sleep_ms(1000) # 等待1000ms
                            continue
                        await asyncio.sleep_ms(200) # 等待200ms
                else:
                    if not await self.send_obd_command(self.pidCmd.multi_cmd_bytes):
                        await asyncio.sleep_ms(2000)
                        continue
            
                # 使用独立计数器控制skip_multi命令发送
                self.skip_counter += 1
                if self.skip_counter >= 10:
                    for k in self.pidCmd.cmd_map:
                        if "skip_multi" in self.pidCmd.cmd_map[k]:
                            cmd_bytes = self.pidCmd.cmd_map[k]["cmd"]
                            if not await self.send_obd_command(cmd_bytes):
                                continue
                            await asyncio.sleep_ms(500)
                    self.skip_counter = 0  # 重置计数器

            except Exception as e:
                print('collect_data error:', e)
                if not self.obd_via_espnow and self.bo:
                    await self.bo.disconnect()

            await asyncio.sleep_ms(200)
            
        # 确保在退出时清理loading动画
        if hasattr(self, 'loading') and self.loading:
            self.loading.delete()
            self.loading = None
            
        print("collect data end")
    async def esp_now_recv(self):
        """esp_now接收数据"""
        while self._running:
            try:
                self.espn.Recv()
            except Exception as e:
                print('esp_now_recv error:', e)
            await asyncio.sleep_ms(10)
        print("esp_now_recv end")
    async def broadcast_data(self):
        """广播数据任务"""
        while self._running:
            #try:
            if not self.data_manager.broadcast_data_empty():
                data = self.data_manager.get_broadcast_data()
                if self.espn:
                    self.espn.Send(self.bcast, data, False)
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
                # 处理车门状态
                if v["pid"] == 'D0':
                    self.update_door_status(v["value"])
                    return
                    
                # 处理档位状态
                if v["pid"] == 'D1':
                    self.update_gear_status(v["value"])
                    return
                    
                # 处理转向灯状态
                if v["pid"] == 'D2':
                    self.update_blinker_status(v["value"])
                    return
                    
                # 处理驾驶模式 (PID: D4)
                if v["pid"] == 'D4':
                    if isinstance(v["value"], list) and len(v["value"]) >= 2:
                        drive_mode = v["value"][1]  # 第二个字节是驾驶模式
                        self.update_drive_mode(drive_mode)  # 使用update_drive_mode函数处理
                    return
                    
                # 原有的显示逻辑
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

    async def test_data(self):
        resp = {"pid": '0D', 'value': 100}
        while self._running:
            resp['value'] += 1
            self.on_show(resp)
            await asyncio.sleep_ms(10)

    def start_tasks(self):
        """启动所有异步任务"""
        run_tasks = []
        if self.is_master():
            run_tasks = [
                self.collect_data,
                #self.test_data,
                self.ble_recv_task,  # 添加接收任务
                self.esp_now_recv,
                self.parse_data,
                self.display_data,
                self.broadcast_data,
            ]
        else:
            run_tasks = [
                self.esp_now_recv,
                self.parse_data,
                self.display_data,
            ]
        for task_func in run_tasks:
            self.tasks.append(asyncio.create_task(task_func()))
        '''
        self.tasks = [
            #asyncio.create_task(self.collect_data()),
            asyncio.create_task(self.parse_data()),
            asyncio.create_task(self.display_data()),
            asyncio.create_task(self.broadcast_data()),
        ]
        '''
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
        # 首先停止所有异步任务
        self._running = False
        
        # 清理转向灯相关资源
        if hasattr(self, 'blinker_timer') and self.blinker_timer:
            self.blinker_timer.delete()
            self.blinker_timer = None
        
        # 等待异步任务完成
        if self.tasks:
            asyncio.gather(*self.tasks)
            print("after gather")
            self.tasks.clear()
        
        # 清理蓝牙连接
        if self.bo:
            self.bo.close()
            self.bo = None
        
        # 清理ESP-NOW
        if self.espn:
            self.espn.destroy()
            self.espn = None
        
        # 移除事件回调
        if hasattr(self, 'arc'):
            self.deinit_event()
        
        # 清理数据管理相关对象
        self.data_manager = None
        self.es = None
        self.pidCmd = None
        
        # 清理转向灯弧形对象引用
        if hasattr(self, 'blinker_arcs'):
            self.blinker_arcs.clear()
        
        # 清理车门标签对象引用
        if hasattr(self, 'door_labels'):
            self.door_labels.clear()
        
        # 清理档位标签对象引用
        self.gear_label = None
        
        # 最后调用父类的 destroy 方法清理UI元素
        try:
            super().destroy()
        except Exception as e:
            print(f"Error in super().destroy(): {e}")

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
                self.unit_label.align(lv.ALIGN.CENTER, x_offset, 15)
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

    async def ble_recv_task(self):
        """接收数据的协程"""
        if  self.obd_via_espnow:
            return
        while self._running:
            try:
                if not self.bo.is_connected:
                    await asyncio.sleep_ms(100)
                    continue
                    
                # 接收数据
                data = await self.bo.receive()
                if data is not None:
                    print("Received:", data)
                    self.data_manager.put_pre_parse_data(data)
                    self.data_manager.put_broadcast_data(data)
                    
            except Exception as e:
                print(f"Receive error: {e}")
                await asyncio.sleep_ms(1000)
                
        print("recv task end")

    def genDoorLabels(self):
        """生成车门状态标签"""
        # 加载车门开启图片
        with open('%s/open_door2.png' % self.script_path, 'rb') as f:
            door_png_data = f.read()
        
        self.door_img_dsc = lv.image_dsc_t({
            'data_size': len(door_png_data),
            'data': door_png_data 
        })

        # 定义四个位置，以屏幕中心为参考点
        positions = {
            'fl': {'align': lv.ALIGN.CENTER, 'x': -90, 'y': -90},  # 左前门
            'fr': {'align': lv.ALIGN.CENTER, 'x': 90, 'y': -90},   # 右前门
            'rl': {'align': lv.ALIGN.CENTER, 'x': -90, 'y': 90},   # 左后门
            'rr': {'align': lv.ALIGN.CENTER, 'x': 90, 'y': 90}     # 右后门
        }
        
        # 创建图片对象
        for door, pos in positions.items():
            img = lv.image(self.screen)
            img.set_src(self.door_img_dsc)
            img.align(pos['align'], pos['x'], pos['y'])
            img.add_flag(lv.obj.FLAG.HIDDEN)  # 默认隐藏
            self.door_labels[door] = img
            self.elements.append(img)

    def genGearLabel(self):
        """生成档位显示标签"""
        self.gear_label = lv.label(self.screen)
        # 使用大字体
        self.gear_label.set_style_text_font(self.myfont_en_50, 0)
        self.gear_label.set_style_text_color(lv.color_hex(0xFFFFFF), 0)
        # 在圆形屏幕底部居中显示，以屏幕中心为参考点
        self.gear_label.align(lv.ALIGN.CENTER, 0, -70)  # 向下偏移120像素
        self.gear_label.set_text("")  # 默认空文本
        self.elements.append(self.gear_label)

    def update_door_status(self, door_status):
        """更新车门状态显示"""
        if not isinstance(door_status, dict):
            return
            
        # 更新每个车门的显示状态
        for door in ['fl', 'fr', 'rl', 'rr']:
            if door in self.door_labels:
                if door_status.get(door, False):
                    self.door_labels[door].remove_flag(lv.obj.FLAG.HIDDEN)
                else:
                    self.door_labels[door].add_flag(lv.obj.FLAG.HIDDEN)
                    
        # 特殊处理后备箱
        if door_status.get('trunk', False):
            # 如果需要，可以添加后备箱开启的显示逻辑
            pass

    def update_gear_status(self, gear):
        """更新档位显示"""
        if not isinstance(gear, str):
            return
            
        if hasattr(self, 'gear_label') and self.gear_label:
            self.gear_label.set_text(gear)

    def genBlinkerArcs(self):
        """生成转向灯弧形"""
        # 左转向灯弧形
        self.blinker_arcs['left'] = lv.arc(self.screen)
        left_arc = self.blinker_arcs['left']
        left_arc.set_size(320, 320)
        left_arc.center()
        left_arc.set_bg_angles(165, 195)  # 左侧弧形
        left_arc.set_angles(165, 195)

        # 设置基本样式
        left_arc.set_style_bg_opa(lv.OPA.TRANSP, lv.PART.MAIN)
        left_arc.set_style_arc_width(6, lv.PART.MAIN)
        left_arc.remove_style(None, lv.PART.KNOB)
        left_arc.set_style_arc_color(lv.color_hex(0x00FF00), lv.PART.MAIN)
        left_arc.remove_style(None, lv.PART.INDICATOR)
        
        # 完全禁用交互
        left_arc.add_flag(lv.obj.FLAG.HIDDEN)  # 默认隐藏
        left_arc.add_flag(lv.obj.FLAG.IGNORE_LAYOUT)  # 忽略布局
        left_arc.add_flag(lv.obj.FLAG.FLOATING)  # 浮动模式
        left_arc.remove_flag(lv.obj.FLAG.CLICKABLE)  # 禁用点击
        left_arc.remove_flag(lv.obj.FLAG.SCROLLABLE)  # 禁用滚动
        left_arc.remove_flag(lv.obj.FLAG.CLICK_FOCUSABLE)  # 禁用焦点
        left_arc.add_flag(lv.obj.FLAG.EVENT_BUBBLE)  # 允许事件冒泡到父对象
        
        # 右转向灯弧形
        self.blinker_arcs['right'] = lv.arc(self.screen)
        right_arc = self.blinker_arcs['right']
        right_arc.set_size(320, 320)
        right_arc.center()
        right_arc.set_bg_angles(345, 15)  # 右侧弧形
        right_arc.set_angles(345, 15)

        # 设置基本样式
        right_arc.set_style_bg_opa(lv.OPA.TRANSP, lv.PART.MAIN)
        right_arc.set_style_arc_width(6, lv.PART.MAIN)
        right_arc.remove_style(None, lv.PART.KNOB)
        right_arc.set_style_arc_color(lv.color_hex(0x00FF00), lv.PART.MAIN)
        right_arc.remove_style(None, lv.PART.INDICATOR)
        
        # 完全禁用交互
        right_arc.add_flag(lv.obj.FLAG.HIDDEN)  # 默认隐藏
        right_arc.add_flag(lv.obj.FLAG.IGNORE_LAYOUT)  # 忽略布局
        right_arc.add_flag(lv.obj.FLAG.FLOATING)  # 浮动模式
        right_arc.remove_flag(lv.obj.FLAG.CLICKABLE)  # 禁用点击
        right_arc.remove_flag(lv.obj.FLAG.SCROLLABLE)  # 禁用滚动
        right_arc.remove_flag(lv.obj.FLAG.CLICK_FOCUSABLE)  # 禁用焦点
        right_arc.add_flag(lv.obj.FLAG.EVENT_BUBBLE)  # 允许事件冒泡到父对象

        self.elements.extend([left_arc, right_arc])

    def blinker_timer_cb(self, timer):
        """转向灯闪烁定时器回调"""
        if not self.blinker_timer:
            return
        
        self.blinker_state = not self.blinker_state
        
        # 根据当前闪烁状态和转向灯状态来控制显示/隐藏
        if self.blinker_state:
            # 显示阶段：根据实际转向灯状态显示
            if hasattr(self, '_left_blinker') and self._left_blinker:
                self.blinker_arcs['left'].remove_flag(lv.obj.FLAG.HIDDEN)
            if hasattr(self, '_right_blinker') and self._right_blinker:
                self.blinker_arcs['right'].remove_flag(lv.obj.FLAG.HIDDEN)
        else:
            # 隐藏阶段：隐藏所有转向灯
            self.blinker_arcs['left'].add_flag(lv.obj.FLAG.HIDDEN)
            self.blinker_arcs['right'].add_flag(lv.obj.FLAG.HIDDEN)

    def update_blinker_status(self, scm_status):
        """更新转向灯状态"""
        if not isinstance(scm_status, dict):
            return
            
        # 保存转向灯状态
        self._left_blinker = scm_status.get('left_blinker', False)
        self._right_blinker = scm_status.get('right_blinker', False)
        
        # 管理定时器
        need_timer = self._left_blinker or self._right_blinker
        has_timer = self.blinker_timer is not None
        
        if need_timer and not has_timer:
            # 需要定时器但没有时，创建定时器
            self.blinker_timer = lv.timer_create(self.blinker_timer_cb, 300, None)
            self.blinker_state = True
        elif not need_timer and has_timer:
            # 不需要定时器但有时，删除定时器
            self.blinker_timer.delete()
            self.blinker_timer = None
            # 确保两个转向灯都隐藏
            self.blinker_arcs['left'].add_flag(lv.obj.FLAG.HIDDEN)
            self.blinker_arcs['right'].add_flag(lv.obj.FLAG.HIDDEN)

    def update_drive_mode(self, mode):
        """更新驾驶模式显示"""
        # 驾驶模式映射
        mode_map = {
            0: "NORMAL",
            1: "SPORT",
            2: "ECO",
            3: "SNOW"
        }
        
        # 更新圆环颜色
        if hasattr(self, 'arc'):
            if mode == 1:  # SPORT模式
                self.setColorWheelColor(0x0000ff)  # 红色 (BGR: 0x0000ff)
            elif mode == 0:  # NORMAL模式
                self.setColorWheelColor(0x00a5ff)  # 橙色 (BGR: 0x00a5ff)

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