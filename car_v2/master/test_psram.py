import esp32
import gc

def check_psram():
    print("\nPSRAM 状态检查:")
    
    # 检查是否有PSRAM
    try:
        psram_size = esp32.get_memory_info('psram')
        print(f"PSRAM 总大小: {psram_size/1024:.1f}KB")
    except Exception as e:
        print("无法获取PSRAM信息，可能未启用: ", e)
    
    # 打印内存信息
    print("\n内存使用情况:")
    free_mem = gc.mem_free()
    alloc_mem = gc.mem_alloc()
    total_mem = free_mem + alloc_mem
    print(f"空闲内存: {free_mem/1024:.1f}KB")
    print(f"已用内存: {alloc_mem/1024:.1f}KB")
    print(f"总内存: {total_mem/1024:.1f}KB")

if __name__ == "__main__":
    check_psram() 