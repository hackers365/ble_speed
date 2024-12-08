class ELM327Stream:
    def __init__(self, on_show):
        self.buffer = bytearray()
        self.on_show = on_show

    def append(self, data):
        """
        将新接收到的数据添加到缓冲区中，并尝试解析完整的响应行。
        
        参数:
        data (bytes): 新接收到的数据
        """
        self.buffer.extend(data)
        
        #print(data)

        if self.buffer.endswith('>'):
            self.buffer = self.buffer[:-1]
        if self.buffer.startswith(b'>'):
            self.buffer = self.buffer[1:]

        # 尝试从缓冲区解析出每一行响应
        while b'\r\r' in self.buffer:
            line, self.buffer = self.buffer.split(b'\r\r', 1)
            if len(line) == 0:
                continue
            cmd, resp = line.split(b'\r', 1)
            if len(cmd) == 0 or len(resp) == 0:
                continue
            parsed_response = self._parse_response(cmd, resp)
            if parsed_response:
                self.on_show(parsed_response)
                #self._handle_parsed_response(parsed_response)

    def _parse_response(self, cmd, response):
        """
        解析单行 ELM327 响应数据。
        
        参数:
        response (bytes): 单行 ELM327 响应
        
        返回:
        dict: 包含 PID 和解析后的值, 如果解析失败返回 None.
        """
        
        raw_response = response.strip()
        clean_response = bytearray(b for b in raw_response if b != ord(' '))

        if clean_response.startswith('41'):
            pid = clean_response[2:4]
            data = clean_response[4:]

            if pid == '0D':  # 车辆速度
                value = int(data[:2].decode(), 16)
                return {'pid': pid, 'value': int(value)}
            
            elif pid == '0C':  # 引擎转速
                a = int(data[:2].decode(), 16)
                b = int(data[2:4].decode(), 16)
                value = (a * 256 + b) / 4
                return {'pid': pid, 'value': int(value)}
            elif pid == '05':  # 水温
                raw_temp = int(data[:2].decode(), 16)
                coolant_temp = raw_temp - 40
                return {'pid': pid, 'value': int(coolant_temp)}
            elif pid == '5C':  # 油温
                raw_temp = int(data[:2].decode(), 16)
                coolant_temp = raw_temp - 40
                return {'pid': pid, 'value': int(coolant_temp)}
            else:
                return None
        else:
            if cmd == 'ATRV':
                return {'pid': 'RV', 'value': clean_response.decode()}
        return None

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
]


# 模拟逐步接收数据
for data in data_stream:
    elm327_stream.append(data)
'''