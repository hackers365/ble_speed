
class Cmd():
    def __init__(self):
        self.init_cmd()
    def init_cmd(self):
        self.last_cmd_type = 0
        self.cmd_type = 1
        self.cmd_map = {
            0: {"cmd": b"010C", "pid": bytearray(b'0C'), "len": 4, "title": "Engine Speed", "unit": "rpm"},
            1: {"cmd": b"010D", "pid": bytearray(b'0D'), "len": 2,"title": "Speed", "unit": "km/h"},
            2: {"cmd": b"ATRV", "pid": bytearray(b'RV'), "title": "voltage", "unit": ""},
            3: {"cmd": b"0105", "pid": bytearray(b'05'), "len": 2,"title": "water temp", "unit": "°C"},
            #4: {"cmd": b"015C\r\n", "pid": bytearray(b'5C'), "len": 2,"title": "oil temp", "unit": "°C"}
        }
        self.pid2value = {
            b"0C": {"pid": '0C', 'value': 38},
            b"0D": {"pid": '0D', 'value': 100},
            b"05": {"pid": '05', 'value': 99},
            b"RV": {"pid": 'RV', 'value': "14.2V"}
        }
    def same_cmd_type(self):
        return self.cmd_type == self.last_cmd_type