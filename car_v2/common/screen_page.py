import usys as sys
sys.path.append('/common')

import micropython, gc
import time
import math

from hardware import display, touch
import lvgl as lv
import lvgl_esp32
import fs_driver
import cmd

from pages.main_page import MainPage
from pages.second_page import SecondPage

class PageManager:
    def __init__(self, container):
        self.screen = container
        self.pages = []
        self.current_page_index = 0
        print("PageManager initialized")
        
    def add_page(self, page):
        self.pages.append(page)
        
    def switch_to_page(self, index):
        if 0 <= index < len(self.pages):
            # 销毁当前页面元素
            if self.current_page_index < len(self.pages):
                self.pages[self.current_page_index].destroy()
            
            self.current_page_index = index
            # 初始化新页面
            self.pages[index].init()

    def handle_touch(self, event):
        code = event.get_code()
        if code == lv.EVENT.PRESSED:
            # 获取按下时的坐标
            indev = lv.indev_get_act()
            if indev:
                point = lv.point_t()
                indev.get_point(point)
                self.touch_start_x = point.x
                print(f"Touch start at x={point.x}")
                
        elif code == lv.EVENT.PRESSING:
            # 获取移动时的坐标
            indev = lv.indev_get_act()
            if indev and hasattr(self, 'touch_start_x'):
                point = lv.point_t()
                indev.get_point(point)
                self.current_x = point.x
                print(f"Moving at x={point.x}")
                
        elif code == lv.EVENT.RELEASED:
            # 计算滑动距离并切换页面
            if hasattr(self, 'touch_start_x') and hasattr(self, 'current_x'):
                diff_x = self.current_x - self.touch_start_x
                print(f"Final diff_x={diff_x}")
                
                # 设置滑动阈值
                threshold = 40
                
                # 根据滑动方向切换页面
                if abs(diff_x) > threshold:
                    if diff_x > 0:
                        # 右滑，切换到上一页
                        next_index = (self.current_page_index - 1) % len(self.pages)
                        print(f"Swipe right, switching to page {next_index}")
                        self.switch_to_page(next_index)
                    else:
                        # 左滑，切换到下一页
                        next_index = (self.current_page_index + 1) % len(self.pages)
                        print(f"Swipe left, switching to page {next_index}")
                        self.switch_to_page(next_index)

class Screen():
    def __init__(self):
        self.init_screen()
        self.init_font()
        self.init_cmd()
        
        # 创建一个全屏容器来接收事件
        self.container = lv.obj(self.screen)
        self.container.set_size(lv.pct(100), lv.pct(100))  # 使用全屏尺寸
        self.container.align(lv.ALIGN.CENTER, 0, 0)
        self.container.set_style_bg_opa(0, 0)  # 设置透明背景
        
        # 添加必要的标志
        self.container.add_flag(lv.obj.FLAG.CLICKABLE)
        self.container.add_flag(lv.obj.FLAG.GESTURE_BUBBLE)  # 允许手势冒泡
        
        # 初始化页面管理器
        self.page_manager = PageManager(self.container)
        
        # 注册手势事件
        self.container.add_event_cb(self.page_manager.handle_touch, lv.EVENT.PRESSED, None)
        self.container.add_event_cb(self.page_manager.handle_touch, lv.EVENT.PRESSING, None)
        self.container.add_event_cb(self.page_manager.handle_touch, lv.EVENT.RELEASED, None)
        
        # 添加页面
        self.page_manager.add_page(MainPage(self))
        self.page_manager.add_page(SecondPage(self))
        
        # 显示第一个页面
        self.page_manager.switch_to_page(0)

    def init_cmd(self):
        self.cmd = cmd.Cmd()

    def init_screen(self):
        wrapper = lvgl_esp32.Wrapper(display, touch)
        wrapper.init()

        display.brightness(60)
        display.swapXY(False)
        display.mirrorX(True)
        display.mirrorY(True)

        touch.swapXY(False)
        touch.mirrorX(True)
        touch.mirrorY(True)

        self.screen = lv.screen_active()
        self.screen.set_style_bg_color(lv.color_hex(0x000000), lv.PART.MAIN | lv.STATE.DEFAULT)
        self.screen.set_style_bg_opa(255, lv.PART.MAIN | lv.STATE.DEFAULT)
        
    def init_font(self):
        try:
            script_path = __file__[:__file__.rfind('/')] if __file__.find('/') >= 0 else '.'
        except NameError:
            script_path = ''
        self.script_path = script_path
        fs_drv = lv.fs_drv_t()
        fs_driver.fs_register(fs_drv, 'S')

        self.myfont_en_100 = lv.binfont_create("S:%s/common/font/speed_num_consolas_100.bin" % script_path)

def Run():
    screen = Screen()
    resp = {"pid": '0D', 'value': 100}

    while True:
        if isinstance(screen.page_manager.pages[screen.page_manager.current_page_index], MainPage):
            screen.page_manager.pages[screen.page_manager.current_page_index].on_show(resp)
            screen.page_manager.pages[screen.page_manager.current_page_index].frame_count += 1
        
        lv.timer_handler_run_in_period(5)
        resp['value'] += 1

if __name__ == '__main__':
    Run()


