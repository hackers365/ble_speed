
class Cmd():
    def __init__(self):
        self.init_cmd()
    def init_cmd(self):
        self.cmd_type = 1
        self.cmd_map = {
            0: {"cmd": b"010C\r\n", "pid": bytearray(b'0C'), "title": "Engine Speed", "unit": "rpm"},
            1: {"cmd": b"010D\r\n", "pid": bytearray(b'0D'), "title": "Speed", "unit": "km/h"},
            2: {"cmd": b"ATRV\r\n", "pid": bytearray(b'RV')},
            3: {"cmd": b"0105\r\n", "pid": bytearray(b'05'), "title": "wanter temp", "unit": "°C"},
            4: {"cmd": b"015C\r\n", "pid": bytearray(b'5C'), "title": "oil temp", "unit": "°C"}
        }