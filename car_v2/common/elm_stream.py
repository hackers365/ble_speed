class ELM327Stream:
    def __init__(self, on_show=None):
        self.buffer = bytearray()
        self.on_show = on_show

    def append(self, data):
        """
        将新接收到的数据添加到缓冲区中，并尝试解析完整的响应行。
        
        参数:
        data (bytes): 新接收到的数据
        """
        self.buffer.extend(data)
        #print(self.buffer)
        
        #print(data)
        '''
        if self.buffer.endswith('>'):
            self.buffer = self.buffer[:-1]
        if self.buffer.startswith(b'>'):
            self.buffer = self.buffer[1:]
        '''
        final_data = []
        # 尝试从缓冲区解析出每一行响应
        while b'>' in self.buffer:
            line, self.buffer = self.buffer.split(b'>', 1)
            if len(line) == 0:
                continue

            if b'\r' in line:
                resps = line.split(b'\r')
            else:
                resps = [line]
            for resp in resps:
                parsed_responses = self._parse_response(resp)
                if parsed_responses:
                    for parse_data in parsed_responses:
                        if self.on_show:
                            self.on_show(parse_data)
                        final_data.append(parse_data)

        return final_data

    def _parse_response(self, response):
        """
        解析单行 ELM327 响应数据。
        
        参数:
        response (bytes): 单行 ELM327 响应
        
        返回:
        dict: 包含 PID 和解析后的值
        """
        ret = []
        raw_response = response.strip()
        clean_response = bytearray(b for b in raw_response if b != ord(' '))
        
        # 扩展帧标识
        if clean_response == b'008':
            return ret
            
        while True:
            if len(clean_response) == 0:
                break
            if clean_response.startswith('01') or clean_response == b'ATRV' or clean_response == b'OK':
                break
            if b':' in clean_response:
                clean_response = clean_response[2:]
                
            pid = clean_response[:2]
            data = clean_response[2:]
            if clean_response.startswith('41'):
                pid = clean_response[2:4]
                data = clean_response[4:]

            skip_count = 0
            if pid == '0D':  # 车辆速度
                value = int(data[:2].decode(), 16)
                ret.append({'pid': pid, 'value': int(value)})
                skip_count = 2
            elif pid == '0C':  # 引擎转速
                a = int(data[:2].decode(), 16)
                b = int(data[2:4].decode(), 16)
                value = (a * 256 + b) / 4
                ret.append({'pid': pid, 'value': int(value)})
                skip_count = 4
            elif pid == '05':  # 水温
                raw_temp = int(data[:2].decode(), 16)
                coolant_temp = raw_temp - 40
                ret.append({'pid': pid, 'value': int(coolant_temp)})
                skip_count = 2
            elif pid == '5C':  # 油温
                raw_temp = int(data[:2].decode(), 16)
                coolant_temp = raw_temp - 40
                ret.append({'pid': pid, 'value': int(coolant_temp)})
                skip_count = 2
            elif pid == 'D0':  # 车门状态
                doors = int(data[:2].decode(), 16)
                value = {
                    'fl': bool(doors & 0x01),  # 左前门
                    'fr': bool(doors & 0x02),  # 右前门
                    'rl': bool(doors & 0x04),  # 左后门
                    'rr': bool(doors & 0x08),  # 右后门
                    'trunk': bool(doors & 0x10)  # 后备箱
                }
                ret.append({'pid': pid, 'value': value})
                skip_count = 2
            elif pid == 'D1':  # 变速箱状态
                gear = int(data[:2].decode(), 16)
                gear_map = {
                    0x01: 'P',
                    0x02: 'R',
                    0x03: 'N',
                    0x04: 'D',
                    0x05: 'S',
                    0x00: ''
                }
                value = gear_map.get(gear, '')
                ret.append({'pid': pid, 'value': value})
                skip_count = 2
            elif pid == 'D2':  # SCM状态
                scm = int(data[:2].decode(), 16)
                value = {
                    'driver_door': bool(scm & 0x01),     # 驾驶员门
                    'left_blinker': bool(scm & 0x02),    # 左转向灯
                    'right_blinker': bool(scm & 0x04),   # 右转向灯
                    'main_on': bool(scm & 0x08),         # MAIN开关
                    'cmbs_state': (scm >> 4) & 0x03      # CMBS状态
                }
                ret.append({'pid': pid, 'value': value})
                skip_count = 2
            elif pid == 'D3':  # 转向传感器状态
                # 解析4字节数据
                angle_high = int(data[:2].decode(), 16)
                angle_low = int(data[2:4].decode(), 16)
                rate = int(data[4:6].decode(), 16)
                sensor_status = int(data[6:8].decode(), 16)
                
                # 计算实际值
                steer_angle = ((angle_high << 8) | angle_low) / 10.0  # 转向角
                steer_rate = rate * 10.0  # 角速度
                
                value = {
                    'angle': steer_angle,           # 转向角(度)
                    'rate': steer_rate,            # 角速度(度/秒)
                    'sensor_status': sensor_status  # 传感器状态
                }
                ret.append({'pid': pid, 'value': value})
                skip_count = 8
                
            elif pid == 'D4':  # 驾驶模式和ECON状态
                econ_status = int(data[:2].decode(), 16)  # 第一个字节: ECON状态
                drive_mode = int(data[2:4].decode(), 16)  # 第二个字节: 驾驶模式
                value = [econ_status, drive_mode]  # 返回原始值列表
                ret.append({'pid': pid, 'value': value})
                skip_count = 4
                
            if b'V' in clean_response:
                ret.append({'pid': 'RV', 'value': clean_response.decode()})
                break
                
            # 向后移动
            if skip_count > 0:
                clean_response = data[skip_count:]
                continue
            clean_response = clean_response[2:]
            
        return ret

    def _handle_parsed_response(self, parsed_response):
        """
        处理解析后的响应数据。在这里可以将解析结果打印出来或存储到某个地方。
        
        参数:
        parsed_response (dict): 解析后的响应数据
        """
        #self.on_show(parsed_response)
        #print(parsed_response)
        return


# 示例使用:
'''
def on_show(v):
    print(v)

elm327_stream = ELM327Stream(on_show)

# 模拟接收到的数据流

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


data_stream = [
    b'410C0C140D00\r410C0C1C0D00\r\r>',
    b'410C0BEA0D00\r410C0BE40D00\r\r>',
    b'410C0BF80D00\r410C0BFC0D00\r\r>',
]

data_stream = [
    b'410C0BA20D00\r008\r0:410C0BA00D00\r1:05735555555555\r\r>'
]


# 模拟逐步接收数据
for data in data_stream:
    elm327_stream.append(data)
'''
