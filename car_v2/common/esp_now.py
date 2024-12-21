import time
import network
import espnow

class EspN:
    def __init__(self, on_recv):
        # A WLAN interface must be active to send()/recv()
        self.on_recv = on_recv

    def Run(self):
        self.sta = network.WLAN(network.STA_IF)
        self.sta.active(True)
        self.sta.disconnect()   # Because ESP8266 auto-connects to last Access Point
        
        self.e = espnow.ESPNow()
        self.e.active(True)
    
    def Recv(self):
        host, msg  = self.e.recv(0)
        if msg:
            self.on_recv(host, msg)
    
    def AddPeer(self, mac):
        self.e.add_peer(mac)
    
    def Send(self, mac, msg, sync):
        self.e.send(mac, msg, sync)

def recv(mac, msg):
     print(str(msg))

# 示例使用:
def start_broadcast():
    e = EspN(recv)
    e.Run()
    while True:
        e.Recv()
        
            
#start_broadcast()
