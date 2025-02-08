from common.ble_obd import BleScan
import time

def on_devices_found(devices):
    """扫描到设备的回调"""
    print("\n发现设备:")
    for _, addr, name, rssi in devices:
        print(f"地址: {addr}, 名称: {name}, 信号强度: {rssi}dB")

def on_scan_complete():
    """扫描完成的回调"""
    print("\n扫描完成!")

def main():
    print(gc.mem_free())
    scanner = BleScan()
    print("开始扫描蓝牙设备...")
    
    # 开始扫描，设置15秒超时
    scanner.start_scan(
        callback=on_devices_found,
        duration_ms=15000,
        completion_callback=on_scan_complete
    )
    
    # 等待扫描完成
    time.sleep(20)
    
    scanner.disconnect()
    
    print("disconnect")
    
    print(gc.mem_free())
    scanner = BleScan()
    print("开始扫描蓝牙设备...")
    
    # 开始扫描，设置15秒超时
    scanner.start_scan(
        callback=on_devices_found,
        duration_ms=15000,
        completion_callback=on_scan_complete
    )

if __name__ == "__main__":
    main() 