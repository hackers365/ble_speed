
class Cmd():
    def __init__(self):
        self.init_cmd()
    def init_cmd(self):
        self.cmd_type = 1
        self.cmd_map = {
            0: {"cmd": b"010C\r\n", "pid": bytearray(b'0C'), "len": 4, "title": "Engine Speed", "unit": "rpm"},
            1: {"cmd": b"010D\r\n", "pid": bytearray(b'0D'), "len": 2,"title": "Speed", "unit": "km/h"},
            2: {"cmd": b"ATRV\r\n", "pid": bytearray(b'RV'), "title": "", "unit": ""},
            3: {"cmd": b"0105\r\n", "pid": bytearray(b'05'), "len": 2,"title": "wanter temp", "unit": "°C"},
            4: {"cmd": b"015C\r\n", "pid": bytearray(b'5C'), "len": 2,"title": "oil temp", "unit": "°C"}
        }