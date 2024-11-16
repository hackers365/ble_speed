import network
import espnow
import time
from ble import demo

# A WLAN interface must be active to send()/recv()
sta = network.WLAN(network.STA_IF)  # Or network.AP_IF
sta.active(True)
sta.disconnect()      # For ESP8266


e = espnow.ESPNow()
e.active(True)

#peer = b'\xbb\xbb\xbb\xbb\xbb\xbb'   # MAC address of peer's wifi interface
#e.add_peer(peer)      # Must add_peer() before send()

peer = b'\xff\xff\xff\xff\xff\xff'
e.add_peer(peer)      # Must add_peer() before send()


demo()

start_time_ms = time.ticks_ms()  # 获取开始时间
print(start_time_ms)
e.send(peer, "Starting...")
for i in range(10000):
    print("send data ", i)
    e.send(peer, str(i), False)
    time.sleep_ms(1000)
#e.send(peer, b'end')

end_time_ms = time.ticks_ms()     # 获取结束时间
execution_time_ms = time.ticks_diff(end_time_ms, start_time_ms)
print("函数执行时间（毫秒）：", execution_time_ms)
