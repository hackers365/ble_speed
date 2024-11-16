import elm_stream
import esp_now
import time

class Display:
    def __init__(self):
        pass
    def Run(self):
        self.epn = esp_now.EspN(self.esp_now_recv)
        self.epn.Run()

        bcast = b'\xff\xff\xff\xff\xff\xff'
        self.epn.AddPeer(bcast)
        
        #init elm_stream
        self.es = elm_stream.ELM327Stream(self.on_show)
        while True:
            self.epn.Recv()
            time.sleep(0.1)

    def esp_now_recv(self, mac, msg):
        self.es.append(msg)

    def on_show(self, v):
        print(v)

def run():
    d = Display()
    d.Run()

run()