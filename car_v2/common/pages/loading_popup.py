import lvgl as lv
from .base_page import BasePage
import bluetooth
import gc
from common.config import Config
import time
from common.aioble_obd import AioBleObd
import asyncio
from ble_obd import BleScan  # 保留旧的导入以保持兼容性

class LoadingPopup(BasePage):
    def __init__(self, baseScreen):
        super().__init__(baseScreen)
        self.ble_scanner = None
        self.lottie = None
        self.found_devices = []  # 存储设备信息
        self.list = None
        # 使用 Screen 的配置对象
        self.config = self.baseScreen.get_config()
        
        # 从配置文件获取UUID
        ble_config = self.config.get_bluetooth_config()
        self.service_uuid = ble_config.get('uuid', "")
        self.rx_char_uuid = ble_config.get('rx_char', "")
        self.tx_char_uuid = ble_config.get('tx_char', "")
        
    def init(self):
        super().init()

        # 创建标题
        title = lv.label(self.screen)
        title.set_text("扫描蓝牙设备")
        title.align(lv.ALIGN.TOP_MID, 0, 40)
        title.set_style_text_color(lv.color_hex(0x000000), 0)
        title.set_style_text_font(lv.font_montserrat_20, 0)
        self.elements.append(title)
        
        print("before start_scan")
        # 开始扫描
        asyncio.create_task(self.start_scan())
        
    async def start_scan(self):
        """开始扫描"""
        if self.ble_scanner:
            await self.ble_scanner.disconnect()
            
        self.lottie = self.show_lottie(self.screen,"/rlottie/loading.json", 150, 150, 0, 0)
        print("before AioBleObd")
        self.ble_scanner = AioBleObd()
        print("after AioBleObd")
        
        # 执行扫描
        self.found_devices = await self.ble_scanner.scan()
        print("Scan complete")
        
        # 扫描完成后的处理
        self.on_scan_complete()
        
    def on_device_select(self, device, addr, name):
        """设备被选中的回调"""
        if self.list:
            self.list.remove_flag(lv.obj.FLAG.CLICKABLE)  # 禁用点击
            
        print(f"\n正在连接设备: {name}")
        
        async def connect_device():
            # 发现服务
            success, service_uuid, tx_uuid, rx_uuid = await self.ble_scanner.discover_uart_service(device)
            
            if success:
                print("\n连接成功！")
                print(f"Service UUID: {service_uuid}")
                print(f"TX UUID: {tx_uuid}")
                print(f"RX UUID: {rx_uuid}")
                
                # 使用 set_bluetooth_config 批量保存配置
                try:
                    # 提取 UUID 字符串的辅助函数
                    def clean_uuid(uuid_str):
                        return str(uuid_str).split("'")[1] if "UUID" in str(uuid_str) else str(uuid_str)
                    
                    self.config.set_bluetooth_config(
                        uuid=clean_uuid(service_uuid),
                        tx_char=clean_uuid(tx_uuid),
                        rx_char=clean_uuid(rx_uuid),
                        device_name=name,
                        device_addr=addr
                    )
                    print("设备信息已保存到配置文件")
                except Exception as e:
                    print(f"保存配置文件失败: {e}")
                
                # 断开连接并关闭弹窗
                def complete():
                    self.ble_scanner.close()
                    self.page_manager.pop_popup()
                self.show_msgbox("save ok", user_callback=complete)
            else:
                self.show_msgbox("connect fail")
                print("连接失败或未发现服务")
                
        # 创建连接任务
        asyncio.create_task(connect_device())
        
    def create_device_list(self):
        """创建设备列表"""
        if self.list:
            self.list.delete()
            
        # 创建设备列表
        self.list = lv.list(self.screen)
        self.list.set_size(240, 240)
        self.list.align(lv.ALIGN.TOP_MID, 0, 80)
        # 设置列表样式
        self.list.set_style_bg_opa(0, 0)
        self.list.set_style_border_width(0, 0)
        self.list.set_style_pad_all(5, 0)
        self.list.set_style_radius(10, lv.PART.ITEMS | lv.STATE.DEFAULT)
        self.list.set_style_bg_color(lv.color_hex(0xf0f0f0), lv.PART.ITEMS | lv.STATE.DEFAULT)
        self.list.set_style_bg_opa(255, lv.PART.ITEMS | lv.STATE.DEFAULT)
        self.list.set_style_text_color(lv.color_hex(0x000000), lv.PART.ITEMS | lv.STATE.DEFAULT)
        self.elements.append(self.list)
        
        # 添加设备到列表
        for device, addr, name, rssi in self.found_devices:
            item = self.list.add_button(lv.SYMBOL.BLUETOOTH, f"{name}\n{addr} ({rssi}dB)")
            item.add_event_cb(
                lambda e, device=device, addr=addr, name=name: 
                self.on_device_select(device, addr, name),
                lv.EVENT.CLICKED, 
                None
            )
        
    def on_scan_complete(self):
        """扫描完成的回调"""
        if self.lottie:
            self.lottie.delete()
            self.lottie = None
        
        # 创建并显示设备列表
        self.create_device_list()

    def destroy(self):
        """页面销毁时清理"""
        if self.ble_scanner:
            self.ble_scanner.close()  # 使用新的 close 方法
        if self.lottie:
            self.lottie.delete()
            self.lottie = None
        super().destroy() 