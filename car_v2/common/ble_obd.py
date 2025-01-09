# This example finds and connects to a peripheral running the
# UART service (e.g. ble_simple_peripheral.py).

# This example demonstrates the low-level bluetooth module. For most
# applications, we recommend using the higher-level aioble library which takes
# care of all IRQ handling and connection management. See
# https://github.com/micropython/micropython-lib/tree/master/micropython/bluetooth/aioble

import bluetooth
import random
import struct
import time
import micropython

from common.ble_advertising import decode_services, decode_name

from micropython import const

_IRQ_CENTRAL_CONNECT = const(1)
_IRQ_CENTRAL_DISCONNECT = const(2)
_IRQ_GATTS_WRITE = const(3)
_IRQ_GATTS_READ_REQUEST = const(4)
_IRQ_SCAN_RESULT = const(5)
_IRQ_SCAN_DONE = const(6)
_IRQ_PERIPHERAL_CONNECT = const(7)
_IRQ_PERIPHERAL_DISCONNECT = const(8)
_IRQ_GATTC_SERVICE_RESULT = const(9)
_IRQ_GATTC_SERVICE_DONE = const(10)
_IRQ_GATTC_CHARACTERISTIC_RESULT = const(11)
_IRQ_GATTC_CHARACTERISTIC_DONE = const(12)
_IRQ_GATTC_DESCRIPTOR_RESULT = const(13)
_IRQ_GATTC_DESCRIPTOR_DONE = const(14)
_IRQ_GATTC_READ_RESULT = const(15)
_IRQ_GATTC_READ_DONE = const(16)
_IRQ_GATTC_WRITE_DONE = const(17)
_IRQ_GATTC_NOTIFY = const(18)
_IRQ_GATTC_INDICATE = const(19)

_ADV_IND = const(0x00)
_ADV_DIRECT_IND = const(0x01)
_ADV_SCAN_IND = const(0x02)
_ADV_NONCONN_IND = const(0x03)

'''
_UART_SERVICE_UUID = bluetooth.UUID("6E400001-B5A3-F393-E0A9-E50E24DCCA9E")
_UART_RX_CHAR_UUID = bluetooth.UUID("6E400002-B5A3-F393-E0A9-E50E24DCCA9E")
_UART_TX_CHAR_UUID = bluetooth.UUID("6E400003-B5A3-F393-E0A9-E50E24DCCA9E")
target_addr = "C8:C9:A3:D5:F1:26"

_UART_SERVICE_UUID = bluetooth.UUID(0x18f0)
_UART_RX_CHAR_UUID = bluetooth.UUID(0x2af1)
_UART_TX_CHAR_UUID = bluetooth.UUID(0x2af0)
target_addr = "C0:48:46:E7:F0:B8"
'''
_UART_SERVICE_UUID = bluetooth.UUID("test")
_UART_RX_CHAR_UUID = bluetooth.UUID("test")
_UART_TX_CHAR_UUID = bluetooth.UUID("test")
target_addr = "test"


class BLESimpleCentral:
    def __init__(self, ble, service_uuid, rx_char_uuid, tx_char_uuid, target_addr):
        self._ble = ble
        self._ble.active(True)
        self._ble.irq(self._irq)
        self._service_uuid = service_uuid
        self._rx_char_uuid = rx_char_uuid
        self._tx_char_uuid = tx_char_uuid
        self._target_addr = target_addr

        self._reset()

    def _reset(self):
        # Cached name and address from a successful scan.
        self._name = None
        self._addr_type = None
        self._addr = None

        # Callbacks for completion of various operations.
        # These reset back to None after being invoked.
        self._scan_callback = None
        self._conn_callback = None
        self._read_callback = None

        # Persistent callback for when new data is notified from the device.
        self._notify_callback = None

        # Connected device.
        self._conn_handle = None
        self._start_handle = None
        self._end_handle = None
        self._tx_handle = None
        self._rx_handle = None

    def _irq(self, event, data):
        if event == _IRQ_SCAN_RESULT:
            addr_type, addr, adv_type, rssi, adv_data = data
            addr_str = ":".join(["{:02X}".format(b) for b in addr])
            print(addr_str)
            if addr_str == self._target_addr:
                print(addr_str)
                print(decode_services(adv_data))
                self._addr_type = addr_type
                self._addr = bytes(addr)
                self._name = decode_name(adv_data) or "?"
                self._ble.gap_scan(None)

        elif event == _IRQ_SCAN_DONE:
            if self._scan_callback:
                if self._addr:
                    # Found a device during the scan (and the scan was explicitly stopped).
                    self._scan_callback(self._addr_type, self._addr, self._name)
                    self._scan_callback = None
                else:
                    # Scan timed out.
                    self._scan_callback(None, None, None)
            self._ble.gap_scan(None)

        elif event == _IRQ_PERIPHERAL_CONNECT:
            print("connect success")
            # Connect successful.
            conn_handle, addr_type, addr = data
            if addr_type == self._addr_type and addr == self._addr:
                self._conn_handle = conn_handle
                self._ble.gattc_discover_services(self._conn_handle)

        elif event == _IRQ_PERIPHERAL_DISCONNECT:
            # Disconnect (either initiated by us or the remote end).
            conn_handle, _, _ = data
            if conn_handle == self._conn_handle:
                # If it was initiated by us, it'll already be reset.
                self._reset()

        elif event == _IRQ_GATTC_SERVICE_RESULT:
            # Connected device returned a service.
            conn_handle, start_handle, end_handle, uuid = data
            print("service", data)
            if conn_handle == self._conn_handle and uuid == self._service_uuid:
                self._start_handle, self._end_handle = start_handle, end_handle

        elif event == _IRQ_GATTC_SERVICE_DONE:
            # Service query complete.
            if self._start_handle and self._end_handle:
                self._ble.gattc_discover_characteristics(
                    self._conn_handle, self._start_handle, self._end_handle
                )
            else:
                print("Failed to find uart service.")

        elif event == _IRQ_GATTC_CHARACTERISTIC_RESULT:
            # Connected device returned a characteristic.
            conn_handle, def_handle, value_handle, properties, uuid = data
            if conn_handle == self._conn_handle and uuid == self._rx_char_uuid:
               self._rx_handle = value_handle
            if conn_handle == self._conn_handle and uuid == self._tx_char_uuid:
                self._tx_handle = value_handle

        elif event == _IRQ_GATTC_CHARACTERISTIC_DONE:
            # Characteristic query complete.
            if self._tx_handle is not None and self._rx_handle is not None:
                # We've finished connecting and discovering device, fire the connect callback.
                if self._conn_callback:
                    self._conn_callback()
            else:
                print("Failed to find uart rx characteristic.")

        elif event == _IRQ_GATTC_WRITE_DONE:
            conn_handle, value_handle, status = data
            print("TX complete")

        elif event == _IRQ_GATTC_NOTIFY:
            conn_handle, value_handle, notify_data = data
            if conn_handle == self._conn_handle and value_handle == self._tx_handle:
                if self._notify_callback:
                    self._notify_callback(notify_data)

    # Returns true if we've successfully connected and discovered characteristics.
    def is_connected(self):
        return (
            self._conn_handle is not None
            and self._tx_handle is not None
            and self._rx_handle is not None
        )

    # Find a device advertising the environmental sensor service.
    def scan(self, callback=None):
        self._addr_type = None
        self._addr = None
        self._scan_callback = callback
        self._ble.gap_scan(10000, 30000, 30000)

    # Connect to the specified device (otherwise use cached address from a scan).
    def connect(self, addr_type=None, addr=None, callback=None):
        self._addr_type = addr_type or self._addr_type
        self._addr = addr or self._addr
        self._conn_callback = callback
        if self._addr_type is None or self._addr is None:
            return False
        self._ble.gap_connect(self._addr_type, self._addr)
        return True

    # Disconnect from current device.
    def disconnect(self):
        if self._conn_handle is None:
            return
        self._ble.gap_disconnect(self._conn_handle)
        self._reset()

    # Send data over the UART
    def write(self, v, response=False):
        if not self.is_connected():
            return False
        self._ble.gattc_write(self._conn_handle, self._rx_handle, v, 1 if response else 0)
        return True

    # Set handler for when data is received over the UART.
    def on_notify(self, callback):
        self._notify_callback = callback


class BleObd:
    def __init__(self, on_value=None, service_uuid=_UART_SERVICE_UUID, rx_char_uuid=_UART_RX_CHAR_UUID, tx_char_uuid=_UART_TX_CHAR_UUID, target_addr=target_addr):
        self.ble = bluetooth.BLE()
        self.central = BLESimpleCentral(self.ble, service_uuid, rx_char_uuid, tx_char_uuid, target_addr)
        self.on_value = on_value
        self.not_found = False
        self.connect_status = 0      #-1: 连接失败 0: 初始化 1:连接中 2:连接成功
    def run(self):
        if self.connect_status >= 1:
            return True
        try:
            self.connect_status = 1
            self.not_found = False
            self.central.disconnect()
            time.sleep(0.1)
            self.central.scan(callback=self.on_scan)
            print('before connected')
            # Wait for connection...
            max_wait_count = 200
            while not self.central.is_connected():
                time.sleep_ms(100)
                if self.not_found:
                    self.connect_status = -1
                    return False
                if max_wait_count <= 0:
                    self.connect_status = -1
                    break
                max_wait_count = max_wait_count - 1

            self.central.on_notify(self.on_rx)

            print("Connected")
            self.connect_status = 2
            return True
        except:
            self.connect_status = -1
            return False
    def send(self, v):
        ret = self.central.write(v, False)
        #print(ret)
        #print(self.connect_status)
        if not ret and self.connect_status == 2:
            self.connect_status = -1
        return ret
        
    def on_scan(self, addr_type, addr, name):
        if addr_type is not None:
            print("Found peripheral:", addr_type, addr, name)
            self.central.connect()
        else:
            self.not_found = True
            print("No peripheral found.")

    def on_rx(self, v):
        recv_value = bytes(v)
        #print('on_rx:'+ str(recv_value))
        if self.on_value:
            self.on_value(recv_value)
        else:
            print(recv_value)
        #elm_manager.append(recv_value)
    def destroy(self):
        try:
            self.central.disconnect()
            self.central = None
            if self.ble and self.ble.active():  # 检查蓝牙是否仍然活跃
                self.ble.active(False)
                print("after ble.active(False)")
            self._reset()
        except Exception as e:
            print(f"销毁BLE时发生错误: {e}")
        finally:
            self.ble = None  # 确保释放蓝牙对象


class BleScan:
    def __init__(self):
        self.ble = bluetooth.BLE()
        self.ble.active(True)
        self.ble.irq(self._irq)
        self._reset()
        
    def _reset(self):
        self._scan_callback = None
        self._completion_callback = None
        self.devices = []  # 存储发现的设备列表 [(addr_type, addr, name, rssi), ...]
        
        # 连接相关
        self._addr_type = None
        self._addr = None
        self._conn_handle = None
        self._services = []  # [(start_handle, end_handle, uuid), ...]
        self._services_uuid = []
        self._current_service_index = 0
        self._tx_char = None
        self._rx_char = None
        self._service_uuid = None
        
        # 连接状态标志
        self._connection_complete = False
        self._connection_success = False
        self._characteristic_discovery_complete = False
        
    def connect(self, addr_type, addr):
        """
        阻塞式连接到指定设备
        :param addr_type: 地址类型
        :param addr: 设备地址
        :return: (success, uuid, tx_char, rx_char)
        """
        try:
            self._connection_complete = False
            self._connection_success = False
            self._characteristic_discovery_complete = False
            self._addr_type = addr_type
            self._addr = addr
            
            # 开始连接
            print("开始连接设备...")
            self.ble.gap_connect(self._addr_type, self._addr)
            
            # 等待连接完成
            timeout = 100  # 10秒超时
            while not self._connection_complete and timeout > 0:
                time.sleep_ms(100)
                timeout -= 1
                
            if timeout <= 0 or not self._connection_success:
                print("连接超时或失败")
                return False, None, None, None
                
            # 等待特征值发现完成
            timeout = 100  # 再次给10秒用于发现服务
            while not self._characteristic_discovery_complete and timeout > 0:
                time.sleep_ms(100)
                timeout -= 1
                
            if timeout <= 0:
                print("发现服务超时")
                self.disconnect()
                return False, None, None, None
                
            if self._tx_char and self._rx_char:
                print("连接成功，服务发现完成")
                return True, self._service_uuid, self._tx_char, self._rx_char
            else:
                print("未找到所需的特征值")
                self.disconnect()
                return False, None, None, None
                
        except Exception as e:
            print(f"连接过程出错: {e}")
            try:
                self.disconnect()
            except:
                pass
            return False, None, None, None
            
    def _irq(self, event, data):
        try:
            if event == _IRQ_SCAN_RESULT:
                addr_type, addr, adv_type, rssi, adv_data = data
                addr_str = ":".join(["{:02X}".format(b) for b in addr])
                name = decode_name(adv_data)
                if not name:
                    name = "Unknown"
                    
                # 检查是否已存在该设备
                for dev in self.devices:
                    if dev[1] == addr_str:
                        return
                        
                self.devices.append((addr_type, addr_str, name, rssi))
                if self._scan_callback:
                    self._scan_callback(self.devices)
                    
            elif event == _IRQ_SCAN_DONE:
                if self._completion_callback:  # 扫描完成时调用完成回调
                    self._completion_callback()
                    
            elif event == _IRQ_PERIPHERAL_CONNECT:
                conn_handle, addr_type, addr = data
                if addr_type == self._addr_type and addr == self._addr:
                    self._conn_handle = conn_handle
                    self._connection_success = True
                    print("连接成功，开始发现服务...")
                    try:
                        self.ble.gattc_discover_services(self._conn_handle)
                    except OSError as e:
                        print("发现服务失败:", e)
                        self._connection_complete = True
                        
            elif event == _IRQ_PERIPHERAL_DISCONNECT:
                conn_handle, _, _ = data
                if conn_handle == self._conn_handle:
                    self._reset()
                    print("设备已断开连接")
                    
            elif event == _IRQ_GATTC_SERVICE_RESULT:
                conn_handle, start_handle, end_handle, uuid = data
                if conn_handle == self._conn_handle:
                    # 直接将 UUID 转换为字符串
                    uuid_str = str(uuid)
                    self._services.append((start_handle, end_handle, uuid_str))
                    
            elif event == _IRQ_GATTC_SERVICE_DONE:
                self._connection_complete = True
                if self._services:
                    print(f"发现了 {len(self._services)} 个服务，开始发现特征值...")
                    self._discover_next_service_characteristics()
                else:
                    print("未找到任何服务")
                    self._characteristic_discovery_complete = True
                    
            elif event == _IRQ_GATTC_CHARACTERISTIC_RESULT:
                conn_handle, def_handle, value_handle, properties, uuid = data
                if conn_handle == self._conn_handle:
                    if properties & 0x10:  # notify 属性
                        self._tx_char = str(uuid)
                    elif properties & 0x08:  # write 属性
                        self._rx_char = str(uuid)
                        
            elif event == _IRQ_GATTC_CHARACTERISTIC_DONE:
                if self._tx_char and self._rx_char:
                    _, _, self._service_uuid = self._services[self._current_service_index]
                    self._characteristic_discovery_complete = True
                    return
                self._current_service_index += 1
                if self._current_service_index < len(self._services):
                    self._discover_next_service_characteristics()
                else:
                    self._characteristic_discovery_complete = True
                    
        except Exception as e:
            print(f"IRQ处理错误: {e}")
            self._connection_complete = True
            self._characteristic_discovery_complete = True
            
    def _discover_next_service_characteristics(self):
        """发现下一个服务的特征值"""
        try:
            if self._current_service_index < len(self._services):
                start_handle, end_handle, uuid = self._services[self._current_service_index]
                #print(f"服务 UUID: {self._services[self._current_service_index]}")
                #print(f"开始发现服务 {self._current_service_index + 1}/{len(self._services)} 的特征值")
                self.ble.gattc_discover_characteristics(
                    self._conn_handle, start_handle, end_handle
                )
            else:
                # 所有服务的特征值都已发现完成
                if self._tx_char and self._rx_char:
                    print("找到完整的UART服务")
                    if self._conn_callback:
                        self._conn_callback(True, self._service_uuid, self._tx_char, self._rx_char)
                else:
                    print("未找到所需的特征值")
                    if self._conn_callback:
                        self._conn_callback(False, None, None, None)
                    self.disconnect()
        except OSError as e:
            print(f"发现特征值失败: {e}")
            if self._conn_callback:
                self._conn_callback(False, None, None, None)
            self.disconnect()
        
    def disconnect(self):
        """断开当前连接"""
        if self._conn_handle is not None:
            try:
                self.ble.gap_disconnect(self._conn_handle)
                return True
            except Exception as e:
                print("断开连接失败:", e)
                return False
        return False
        
    def is_connected(self):
        """检查是否已连接"""
        return self._conn_handle is not None

    def start_scan(self, callback=None, duration_ms=5000, completion_callback=None):
        """
        开始扫描BLE设备
        :param callback: 每发现新设备时的回调函数，参数为设备列表
        :param duration_ms: 扫描持续时间(毫秒)
        :param completion_callback: 扫描完成时的回调函数
        """
        self._reset()
        self._scan_callback = callback
        self._completion_callback = completion_callback
        try:
            # 参数说明：
            # duration_ms: 扫描持续时间
            # interval_us: 扫描间隔 (微秒)
            # window_us: 扫描窗口 (微秒)
            print("before gap_scan")
            self.ble.gap_scan(duration_ms, 30000, 30000)
            print("after gap_scan")
            return True
        except Exception as e:
            print("扫描失败:", e)
            return False
            
    def stop_scan(self):
        """停止扫描"""
        try:
            if self.ble and self.ble.active():  # 检查蓝牙是否仍然活跃
                self.ble.gap_scan(None)
                return True
        except Exception as e:
            print("停止扫描失败:", e)
        return False

    def destroy(self):
        try:
            self.disconnect()
            print("after disconnect")
            if self.ble and self.ble.active():  # 检查蓝牙是否仍然活跃
                self.ble.active(False)
                print("after ble.active(False)")
            self._reset()
        except Exception as e:
            print(f"销毁BLE时发生错误: {e}")
        finally:
            self.ble = None  # 确保释放蓝牙对象
'''
def demo(scr):
    ble = bluetooth.BLE()
    central = BLESimpleCentral(ble)

    not_found = False

    def on_scan(addr_type, addr, name):
        if addr_type is not None:
            print("Found peripheral:", addr_type, addr, name)
            central.connect()
        else:
            nonlocal not_found
            not_found = True
            print("No peripheral found.")

    central.scan(callback=on_scan)
    
    print('before connected')
    # Wait for connection...
    while not central.is_connected():
        time.sleep_ms(100)
        if not_found:
            return

    print("Connected")
    
    def on_rx(v):
        recv_value = bytes(v)
        print(recv_value)
        elm_manager.append(recv_value)

    def on_show(v):
        scr.set_text("100")
        return
        #scr.set_text(str(v['value']))
        #print(v)
    elm_manager = elm_stream.ELM327Stream(on_show)

    central.on_notify(on_rx)

    with_response = False

    cmd_list = ["ATRV", "010D", "010C"]
    while central.is_connected():
        i = 0
        try:
            cmd = cmd_list[i%len(cmd_list)]
            v = str(cmd) + "\r\n"
            central.write(v, with_response)
        except:
            print("TX failed")
        i += 1
        time.sleep_ms(400 if with_response else 30)
'''
    


if __name__ == "__main__":
    # Example with default values
    bo = BleObd()
    bo.run()

    # Example with custom values
    '''
    custom_service_uuid = bluetooth.UUID(0x18f0)
    custom_rx_char_uuid = bluetooth.UUID(0x2af1)
    custom_tx_char_uuid = bluetooth.UUID(0x2af0)
    custom_target_addr = "C0:48:46:E7:F0:B8"
    
    bo = BleObd(
        service_uuid=custom_service_uuid,
        rx_char_uuid=custom_rx_char_uuid,
        tx_char_uuid=custom_tx_char_uuid,
        target_addr=custom_target_addr
    )
    bo.run()
    '''

