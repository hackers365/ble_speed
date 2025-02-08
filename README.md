20241010
固件基于 https://github.com/apexracing/lvgl_esp32_mpy , 将lvgl的双缓冲从内存移至外存 编译成 firmware_ble_optimize_20241010.bin，可以同时开启 wifi, ble, lvgl显示

20250110
优化：
程序
1. master与slave 程序合二为一
2. 新增 扫描 ble obd设备 并保存
3. 新增 master与slave 角色选项

固件
1. wifi active(False)时调用deinit方法，释放dma内存
2. 将lvgl缓存使用 dma 还是 psram 由应用方控制
3. 优化wifi dma内存占到由120k => 60k，ble dma内存占用由60k => 30k
   

使用:
刷入 firmware/firmware_wifi_close_psram_reduce_memory.bin 固件，将car_v2目录下的文件使用thonny上传至圆屏即可

右滑可以 配置扫描蓝牙obd设备
