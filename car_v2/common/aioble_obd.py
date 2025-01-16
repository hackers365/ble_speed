import sys
sys.path.append("/common")

import aioble
import bluetooth
import struct
import time
import asyncio

from micropython import const
from common.ble_advertising import decode_services, decode_name

# 常量定义
SCAN_DURATION_MS = const(10000)    # 扫描持续时间，2秒足够发现设备
SCAN_INTERVAL_US = const(30000)   # 扫描间隔，30ms
SCAN_WINDOW_US = const(15000)     # 扫描窗口，15ms，设为间隔的一半
CONNECT_TIMEOUT_MS = const(5000)  # 连接超时时间，5秒通常足够建立连接

class AioBleObd:
    def __init__(self):
        self._conn = None
        self._rx_char = None  # write characteristic
        self._tx_char = None  # notify characteristic
        self._notify_callback = None
        self.devices = []  # [(device, addr, name, rssi), ...]
        self._connecting = False  # 添加连接状态标志
        self._connect_task = None  # 添加连接任务引用
        
    async def scan(self, duration_ms=SCAN_DURATION_MS):
        """
        扫描BLE设备
        返回设备列表: [(device, addr, name, rssi), ...]
        """
        self.devices.clear()
        async with aioble.scan(duration_ms, interval_us=SCAN_INTERVAL_US, window_us=SCAN_WINDOW_US) as scanner:
            async for result in scanner:
                device = result.device
                addr = device.addr_hex()
                name = result.name() if result.name() else "Unknown"
                rssi = result.rssi

                # 检查是否已存在该设备
                exists = False
                for dev, dev_addr, _, _ in self.devices:
                    if dev_addr == addr:
                        exists = True
                        break
                        
                if not exists:
                    self.devices.append((device, addr, name, rssi))
                    
        return self.devices
        
    async def discover_uart_service(self, device):
        """
        发现设备上的UART服务
        参数:
            device: aioble.Device 对象
        返回: (success, service_uuid, tx_uuid, rx_uuid)
        """
        try:
            # 连接设备
            conn = await device.connect(timeout_ms=CONNECT_TIMEOUT_MS)
            
            async with conn:
                # 先收集所有服务
                services = []
                async for service in conn.services():
                    print("Found service:", service)
                    services.append(service)
                    
                # 遍历收集到的所有服务
                for service in services:
                    tx_char = None
                    rx_char = None
                    
                    # 收集该服务的所有特征值
                    chars = []
                    async for char in service.characteristics():
                        print("Found characteristic:", char)
                        chars.append(char)
                    
                    # 遍历特征值寻找匹配的pair
                    for char in chars:
                        if char.properties & bluetooth.FLAG_NOTIFY:
                            tx_char = char
                            tx_uuid = str(char.uuid).replace('UUID(','').replace(')','').replace("'","")
                        elif (char.properties & bluetooth.FLAG_WRITE) or (char.properties & bluetooth.FLAG_WRITE_NO_RESPONSE):
                            rx_char = char
                            rx_uuid = str(char.uuid).replace('UUID(','').replace(')','').replace("'","")
                            
                        # 如果找到了notify和write特征值
                        if tx_char and rx_char:
                            service_uuid = str(service.uuid).replace('UUID(','').replace(')','').replace("'","")
                            return True, service_uuid, tx_uuid, rx_uuid
                
            return False, None, None, None

        except asyncio.CancelledError:
            print("Service discovery cancelled")
            raise

        except aioble.DeviceDisconnectedError:
            print("Device disconnected during service discovery")
            return False, None, None, None

        except Exception as e:
            print(f"Service discovery error: {e}")
            return False, None, None, None

    async def connect_to_service(self, addr, service_uuid, tx_uuid, rx_uuid):
        """
        连接到指定地址的设备的指定服务
        参数:
            addr: 设备MAC地址字符串
            service_uuid: 服务UUID字符串
            tx_uuid: 通知特征值UUID字符串
            rx_uuid: 写入特征值UUID字符串
        返回: bool 是否连接成功
        """
        if self._connecting:
            print("Already connecting...")
            return False

        self._connecting = True
        self._connect_task = asyncio.current_task()

        # 先扫描找到设备
        device = None
        async with aioble.scan(SCAN_DURATION_MS, interval_us=SCAN_INTERVAL_US, window_us=SCAN_WINDOW_US) as scanner:
            async for result in scanner:
                #都变成大写
                if result.device.addr_hex().upper() == addr.upper():
                    device = result.device
                    break

        if not device:
            print(f"Device {addr} not found")
            await self.disconnect()
            return False

        # 连接设备
        self._conn = await device.connect(timeout_ms=CONNECT_TIMEOUT_MS)
        
        # 转换UUID字符串为UUID对象
        try:
            service_uuid_obj = bluetooth.UUID(service_uuid)
            tx_uuid_obj = bluetooth.UUID(tx_uuid)
            rx_uuid_obj = bluetooth.UUID(rx_uuid)
        except Exception as e:
            print(f"Invalid UUID format: {e}")
            await self.disconnect()
            return False
        
        # 直接获取指定服务
        service = await self._conn.service(service_uuid_obj)
        if not service:
            print("Service not found")
            await self.disconnect()
            return False
            
        # 获取特征值
        self._tx_char = await service.characteristic(tx_uuid_obj)
        self._rx_char = await service.characteristic(rx_uuid_obj)
        
        if self._tx_char and self._rx_char:
            # 启用通知，不需要传递回调
            await self._tx_char.subscribe()
            return True
            
        print("Characteristics not found")
        await self.disconnect()
        return False
        '''
        except asyncio.CancelledError:
            print("Connection cancelled")
            await self.disconnect()
            raise

        except Exception as e:
            print(f"连接服务错误: {e}")
            await self.disconnect()
            return False

        finally:'''
        self._connecting = False
        self._connect_task = None

    async def cancel_connect(self):
        """取消正在进行的连接"""
        if self._connecting and self._connect_task:
            try:
                self._connect_task.cancel()
                await self.disconnect()
                return True
            except Exception as e:
                print(f"取消连接错误: {e}")
        return False

    async def disconnect(self):
        """断开连接"""
        self._connecting = False
        if self._conn:
            try:
                await self._conn.disconnect()
            except:
                pass
            finally:
                self._conn = None
                self._rx_char = None
                self._tx_char = None

    def close(self):
        """完全关闭蓝牙"""
        try:
            # 先断开连接
            if self._conn:
                self._conn.disconnect()
            # 停止 aioble (这会自动关闭蓝牙)
            aioble.stop()
        except Exception as e:
            print(f"Close error: {e}")

    async def send(self, data):
        """
        发送数据
        如果连接断开，返回False
        """
        try:
            if not self._rx_char:
                return False
                
            # 发送数据
            if isinstance(data, str):
                data = data.encode()
            await self._rx_char.write(data)
            return True
            
        except aioble.DeviceDisconnectedError:
            print("Device disconnected during send")
            await self.disconnect()  # 清理连接状态
            return False
            
        except Exception as e:
            print(f"发送数据错误: {e}")
            if "disconnect" in str(e).lower():
                await self.disconnect()
            return False

    def on_notify(self, callback):
        """设置接收数据的回调函数"""
        self._notify_callback = callback
        
    def _on_notify(self, sender, data):
        """通知回调处理"""
        if self._notify_callback:
            self._notify_callback(data)
            
    @property
    def is_connected(self):
        """检查是否已连接"""
        try:
            return (self._conn is not None and 
                   self._conn.is_connected() and 
                   self._rx_char is not None and 
                   self._tx_char is not None)
        except:
            return False

    async def receive(self):
        """
        接收数据
        返回: 接收到的数据或None(如果连接断开)
        """
        try:
            if not self._tx_char:
                return None
                
            # 等待接收数据
            data = await self._tx_char.notified()
            return data
            
        except aioble.DeviceDisconnectedError:
            print("Device disconnected during receive")
            await self.disconnect()
            return None
            
        except Exception as e:
            print(f"接收数据错误: {e}")
            if "disconnect" in str(e).lower():
                await self.disconnect()
            return None


async def scan():
    obd = AioBleObd()
    devices = await obd.scan()
    print("Found devices:", devices)
    
    # 找到名称为"mpy-uart"的设备
    device = None
    for dev in devices:
        print(f"Device: {dev[2]} ({dev[1]})")
        if dev[2] == "mpy-uart":
            device = dev
            break
    
    if device is None:
        print("Device 'mpy-uart' not found")
        return
        
    print(f"Found mpy-uart device: {device[1]}")

    ret, service_uuid, tx_uuid, rx_uuid = await obd.discover_uart_service(device[0])
    if ret:
        print("Found UART service:")
        print(f"Service UUID: {service_uuid}")
        print(f"TX UUID: {tx_uuid}")
        print(f"RX UUID: {rx_uuid}")
    else:
        print("UART service not found")


# 使用示例
async def test():
    obd = AioBleObd()
    
    # 连接设备
    success = await obd.connect_to_service(
        "c8:c9:a3:d5:f1:26",
        "6e400001-b5a3-f393-e0a9-e50e24dcca9e",
        "6e400003-b5a3-f393-e0a9-e50e24dcca9e",
        "6e400002-b5a3-f393-e0a9-e50e24dcca9e"
    )
    
    if success:
        print("Connected successfully!")
        
        # 发送一些测试数据
        await obd.send("ATZ\r\n")
        
        # 接收数据循环
        while True:
            data = await obd.receive()
            if data is None:
                print("Connection lost")
                break
            print("Received:", data)
            
            # 每次接收后等待一小段时间
            await asyncio.sleep_ms(100)
    else:
        print("Connection failed")

# 带超时的连接示例
async def connect_with_timeout(timeout=10):
    addr = "c8:c9:a3:d5:f1:26"
    service_uuid = "6e400001-b5a3-f393-e0a9-e50e24dcca9e"
    tx_uuid = "6e400003-b5a3-f393-e0a9-e50e24dcca9e"
    rx_uuid = "6e400002-b5a3-f393-e0a9-e50e24dcca9e"
    obd = AioBleObd()
    while True:
        print("connecting...")
        print(obd._connecting)
        # 创建连接任务
        success = await obd.connect_to_service(addr, service_uuid, tx_uuid, rx_uuid)
        if success:
            return obd
        await asyncio.sleep_ms(2000)

# 扫描并连接示例
async def scan_and_connect():
    obd = AioBleObd()
    while True:
        devices = await obd.scan()
        print("Found devices:", devices)
        
        # 找到名称为"mpy-uart"的设备
        device = None
        for dev in devices:
            print(f"Device: {dev[2]} ({dev[1]})")
            if dev[2] == "mpy-uart":
                device = dev
                break
        
        if device is None:
            print("Device 'mpy-uart' not found")
            continue
            
        print(f"Found mpy-uart device: {device[1]}")
        
        # 发现服务
        ret, service_uuid, tx_uuid, rx_uuid = await obd.discover_uart_service(device[0])
        if ret:
            print("Found UART service:")
            print(f"Service UUID: {service_uuid}")
            print(f"TX UUID: {tx_uuid}")
            print(f"RX UUID: {rx_uuid}")
            
            # 连接到发现的服务
            if await obd.connect_to_service(device[1], service_uuid, tx_uuid, rx_uuid):
                print("Connected!")
                
                # 发送和接收数据
                while True:
                    await obd.send("ATRV\r\n")
                    data = await obd.receive()
                    if data is None:
                        break
                    print("Received:", data)
                    await asyncio.sleep_ms(100)
        else:
            print("UART service not found")
        await asyncio.sleep_ms(3000)

if __name__ == "__main__":
    asyncio.run(scan())
