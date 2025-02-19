from machine import UART
import network
import espnow
import time
import asyncio

# ELM327常用命令列表
ELM_COMMANDS = {
    'RESET': 'ATZ',
    'ECHO_OFF': 'ATE0',
    'HEADERS_ON': 'ATH1',
    'PROTOCOL_AUTO': 'ATSP0',
    'READ_VIN': '0902',
    'ENGINE_RPM': '010C',
    'VEHICLE_SPEED': '010D',
    'ENGINE_TEMP': '0105'
}

class ELM327Client:
    def __init__(self):
        """初始化ELM327客户端"""
        self.running = True
        
        # 初始化WiFi
        self.wifi = network.WLAN(network.STA_IF)
        if self.wifi.active():
            self.wifi.disconnect()
            self.wifi.active(False)
            time.sleep_ms(500)
        self.wifi.active(True)
        time.sleep_ms(500)  # 等待WiFi初始化完成
        
        # 初始化ESP-NOW
        self.esp_now = espnow.ESPNow()
        self.esp_now.active(True)
        
        # 添加广播peer
        self.BROADCAST_MAC = b'\xff\xff\xff\xff\xff\xff'
        self.esp_now.add_peer(self.BROADCAST_MAC, channel=1)
        
    async def _message_receiver(self):
        """异步接收ESP-NOW消息"""
        print("开始接收消息...")
        while self.running:
            if self.esp_now.any():
                host, msg = self.esp_now.recv()
                try:
                    response = msg.decode()
                    print(response)
                    if response:
                        # 过滤掉命令回显和空行
                        lines = [line.strip() for line in response.split('\r') if line.strip()]
                        valid_responses = [line for line in lines if not line.startswith('>')]
                        if valid_responses:
                            response = valid_responses[-1]  # 使用最后一个有效响应
                            print(f"收到响应: {response}")
                except Exception as e:
                    print(f"处理响应错误: {e}")
            await asyncio.sleep_ms(10)
    
    async def send_command(self, command):
        """广播发送ELM327命令"""
        try:
            if command in ELM_COMMANDS:
                cmd = ELM_COMMANDS[command]
            else:
                cmd = command
            
            # 确保命令以回车符结尾
            if not cmd.endswith('\r'):
                cmd += '\r'
            cmd += '\n>'
                
            # 通过ESP-NOW广播发送命令
            self.esp_now.send(self.BROADCAST_MAC, cmd.encode())
            print(f"已广播命令: {cmd.strip()}")
            
        except Exception as e:
            print(f"发送错误: {e}")
    
    async def read_vin(self):
        """读取车辆VIN码"""
        await self.send_command('READ_VIN')
    
    async def read_engine_rpm(self):
        """读取发动机转速"""
        await self.send_command('ENGINE_RPM')
    
    async def read_vehicle_speed(self):
        """读取车速"""
        await self.send_command('VEHICLE_SPEED')
    
    async def read_engine_temp(self):
        """读取发动机温度"""
        await self.send_command('ENGINE_TEMP')
    
    async def command_sequence(self):
        """执行命令序列"""
        print("开始执行命令序列...")
        print("\n读取发动机转速:")
        await self.read_engine_rpm()
        await asyncio.sleep_ms(500)
        
        print("等待响应中...")
        # 等待最后的响应
        await asyncio.sleep(2)
    
    def close(self):
        """关闭客户端"""
        self.running = False
        self.esp_now.active(False)
        self.wifi.active(False)

async def main():
    print("正在初始化...")
    client = ELM327Client()
    try:
        # 使用gather同时运行消息接收和命令序列
        await asyncio.gather(
            client._message_receiver(),
            client.command_sequence()
        )
    finally:
        client.close()

if __name__ == '__main__':
    asyncio.run(main()) 