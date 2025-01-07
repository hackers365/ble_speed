
class Cmd():
    def __init__(self):
        self.init_cmd()
    def init_cmd(self):
        self.last_cmd_type = 0
        self.cmd_type = 1
        self.cmd_map = {
            0: {"cmd": b"010C\r\n", "pid": bytearray(b'0C'), "len": 4, "default": 0, "title": "Engine Speed", "unit": "rpm"},
            1: {"cmd": b"010D\r\n", "pid": bytearray(b'0D'), "len": 2,"default": 0, "title": "Speed", "unit": "km/h"},
            2: {"cmd": b"ATRV\r\n", "pid": bytearray(b'RV'), "default": "14.2V", "title": "voltage", "unit": ""},
            3: {"cmd": b"0105\r\n", "pid": bytearray(b'05'), "len": 2,"default": 0, "title": "water temp", "unit": "°C"},
            #4: {"cmd": b"015C\r\n", "pid": bytearray(b'5C'), "len": 2,"title": "oil temp", "unit": "°C"}
        }
    def same_cmd_type(self):
        return self.cmd_type == self.last_cmd_type