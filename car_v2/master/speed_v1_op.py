import usys as sys
sys.path.append('/common')

import uasyncio as asyncio
import screen
import lvgl as lv

async def main():
    # 初始化屏幕
    scr = screen.Screen()
    
    # 主循环
    while True:
        lv.timer_handler_run_in_period(5)
        await asyncio.sleep_ms(5)
        

def Run():
    asyncio.run(main())

if __name__ == '__main__':
    Run()


