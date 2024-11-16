
class Cmd():
    def __init__(self):
        self.init_cmd()
    def init_cmd(self):
        self.cmd_type = 1
        self.cmd_map = {
            0: {"cmd": b"010C\r\n", "pid": bytearray(b'0C')},
            1: {"cmd": b"010D\r\n", "pid": bytearray(b'0D')},
            2: {"cmd": b"ATRV\r\n", "pid": bytearray(b'RV')}
        }