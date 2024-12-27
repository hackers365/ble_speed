import usys as sys
sys.path.append('/common')

import micropython, gc
import time
import math

from hardware import display, touch
import lvgl as lv
import lvgl_esp32
import fs_driver

from pages.main_page import MainPage
from pages.second_page import SecondPage

class PageNode:
    def __init__(self, page):
        self.page = page
        self.prev = None
        self.next = None

class PageManager:
    def __init__(self):
        self.head = None          # 链表头节点
        self.current = None       # 当前一级页面节点
        self.popup_stack = []     # 功能页面堆栈
        self.touch_start_x = None
        self.current_x = None
        print("PageManager initialized")
        
    def add_main_page(self, page):
        """添加一级页面到链表"""
        new_node = PageNode(page)
        if not self.head:
            self.head = new_node
            self.current = new_node
            page.init()
        else:
            # 添加到链表末尾
            current = self.head
            while current.next:
                current = current.next
            current.next = new_node
            new_node.prev = current
    
    def switch_main_page(self, direction):
        """切换一级页面，支持循环切换
        direction: 1 表示向前，-1 表示向后
        """
        if not self.current:
            return False
            
        target_node = self.current.next if direction > 0 else self.current.prev
        
        # 如果没有下一个/上一个节点，则循环到链表的另一端
        if not target_node:
            if direction > 0:
                # 向前滑动到尽头时，回到链表头部
                target_node = self.head
            else:
                # 向后滑动到尽头时，找到链表尾部
                target_node = self.head
                while target_node.next:
                    target_node = target_node.next
        
        # 清空功能页面堆栈
        self.clear_popup_stack()
        # 切换页面
        self.current.page.destroy()
        self.current = target_node
        self.current.page.init()
        return True
    
    def push_popup(self, page):
        """压入功能页面"""
        page.is_popup = True  # 标记为功能页面
        if not self.popup_stack:
            # 第一个功能页面不需要销毁前一个
            self.popup_stack.append(page)
            page.init()
        else:
            # 销毁当前功能页面
            self.popup_stack[-1].destroy()
            self.popup_stack.append(page)
            page.init()
    
    def pop_popup(self):
        """弹出功能页面"""
        if self.popup_stack:
            current_popup = self.popup_stack.pop()
            current_popup.destroy()
            # 如果还有功能页面，显示上一个
            if self.popup_stack:
                self.popup_stack[-1].init()
            return True
        return False
    
    def clear_popup_stack(self):
        """清空功能页面堆栈"""
        while self.popup_stack:
            self.pop_popup()
    
    @property
    def current_page(self):
        """获取当前显示的页面"""
        return self.popup_stack[-1] if self.popup_stack else self.current.page if self.current else None

    def handle_touch(self, event):
        code = event.get_code()
        
        # 如果有功能页面，不处理滑动手势
        if self.popup_stack:
            return
            
        if code == lv.EVENT.PRESSED:
            indev = lv.indev_active()
            if indev:
                point = lv.point_t()
                indev.get_point(point)
                self.touch_start_x = point.x
                print(f"Touch start at x={self.touch_start_x}")
                
        elif code == lv.EVENT.PRESSING:
            indev = lv.indev_active()
            if indev and self.touch_start_x is not None:
                point = lv.point_t()
                indev.get_point(point)
                self.current_x = point.x
                print(f"Moving at x={self.current_x}")
                
        elif code == lv.EVENT.RELEASED:
            if self.touch_start_x is not None and self.current_x is not None:
                diff_x = self.current_x - self.touch_start_x
                threshold = 40
                print(f"Release with diff_x={diff_x}")
                
                if abs(diff_x) > threshold:
                    if diff_x > 0:
                        # 右滑，切换到上一个一级页面
                        print("Right swipe: switching to previous page")
                        self.switch_main_page(-1)
                    else:
                        # 左滑，切换到下一个一级页面
                        print("Left swipe: switching to next page")
                        self.switch_main_page(1)
                
                # 重置触摸状态
                self.touch_start_x = None
                self.current_x = None

class Screen():
    def __init__(self): 
        self.init_screen()
        self.init_font()
        
        # 初始化页面管理器
        self.page_manager = PageManager()
        
        # 添加必要的标志
        self.screen.add_flag(lv.obj.FLAG.CLICKABLE)
        self.screen.add_flag(lv.obj.FLAG.GESTURE_BUBBLE)  # 允许手势冒泡
                
        # 注册手势事件
        self.screen.add_event_cb(self.page_manager.handle_touch, lv.EVENT.PRESSED, None)
        self.screen.add_event_cb(self.page_manager.handle_touch, lv.EVENT.PRESSING, None)
        self.screen.add_event_cb(self.page_manager.handle_touch, lv.EVENT.RELEASED, None)
        
        # 添加一级页面
        main_page = MainPage(self)
        second_page = SecondPage(self)
    
        
        # 将一级页面添加到链表
        self.page_manager.add_main_page(main_page)
        self.page_manager.add_main_page(second_page)


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
        
        current_page = screen.page_manager.current_page
        if isinstance(current_page, MainPage):
            current_page.on_show(resp)
            current_page.frame_count += 1
        
        lv.timer_handler_run_in_period(5)
        resp['value'] += 1

if __name__ == '__main__':
    Run()


