import usys as sys
sys.path.append('/common')

import uasyncio as asyncio
import screen
import lvgl as lv

class fps_counter:
    def __init__(self):
        self.last_time = 0
        self.frame_count = 0
        self.fps = 0

    def update(self):
        current_time = lv.tick_get()
        elapsed = current_time - self.last_time
        if elapsed > 0:
            self.fps = (self.frame_count * 1000) / elapsed
            self.last_time = current_time
            self.frame_count = 0

    def get_fps(self):
        return self.fps

async def main():
    fps_instance = fps_counter()
    # 初始化屏幕
    scr = screen.Screen(fps_instance)

    # 主循环
    while True:
        lv.timer_handler_run_in_period(5)
        fps_instance.frame_count += 1
        await asyncio.sleep_ms(5)
        

def Run():
    asyncio.run(main())

if __name__ == '__main__':
    Run()


