import common.aioble
import bluetooth
import uasyncio as asyncio
from micropython import const

# UUID 常量定义
_UART_SERVICE_UUID = bluetooth.UUID(0x18f0)
_UART_RX_CHAR_UUID = bluetooth.UUID(0x2af1)
_UART_TX_CHAR_UUID = bluetooth.UUID(0x2af0)
TARGET_ADDR = "C0:48:46:E7:F0:B8"

class BleObd:
    def __init__(self, on_value=None):
        self.on_value = on_value
        self.connect_status = 0  # -1: 连接失败 0: 初始化 1:连接中 2:连接成功
        self.connection = None
        self.rx_characteristic = None
        self.tx_characteristic = None

    async def scan_for_device(self):
        # 扫描指定设备
        async with aioble.scan(5000, interval_us=30000, window_us=30000) as scanner:
            async for device in scanner:
                addr_str = ":".join(["{:02X}".format(b) for b in device.addr])
                if addr_str == TARGET_ADDR:
                    return device
        return None

    async def connect_to_device(self, device):
        # 连接到设备
        self.connection = await device.connect()
        # 发现服务
        async with self.connection:
            services = await self.connection.discover_services()
            uart_service = None
            
            for service in services:
                if service.uuid == _UART_SERVICE_UUID:
                    uart_service = service
                    break
            
            if not uart_service:
                raise ValueError("UART service not found")

            # 获取特征值
            characteristics = await uart_service.discover_characteristics()
            for char in characteristics:
                if char.uuid == _UART_RX_CHAR_UUID:
                    self.rx_characteristic = char
                elif char.uuid == _UART_TX_CHAR_UUID:
                    self.tx_characteristic = char

            if not (self.rx_characteristic and self.tx_characteristic):
                raise ValueError("UART characteristics not found")

    async def notification_handler(self):
        # 处理通知
        async with self.tx_characteristic.notify() as notifications:
            async for value in notifications:
                if self.on_value:
                    self.on_value(bytes(value))
                else:
                    print("Received:", bytes(value))

    async def send(self, data):
        # 发送数据
        if not self.rx_characteristic:
            return False
        try:
            await self.rx_characteristic.write(data)
            return True
        except:
            self.connect_status = -1
            return False

    async def run(self):
        if self.connect_status >= 1:
            return

        try:
            self.connect_status = 1
            
            # 扫描设备
            device = await self.scan_for_device()
            if not device:
                self.connect_status = -1
                print("Device not found")
                return

            # 连接设备
            await self.connect_to_device(device)
            self.connect_status = 2
            print("Connected successfully")

            # 启动通知处理
            await self.notification_handler()

        except Exception as e:
            print("Error:", e)
            self.connect_status = -1
            return False

async def main():
    def on_value(data):
        print("Received data:", data)

    ble = BleObd(on_value=on_value)
    await ble.run()

if __name__ == "__main__":
    asyncio.run(main())