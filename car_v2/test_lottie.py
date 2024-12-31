import usys as sys
sys.path.append('/common') # See: https://github.com/micropython/micropython/issues/6419
sys.path.append('/rlottie') # See: https://github.com/micropython/micropython/issues/6419

from hardware import display,touch

import fs_driver

import lvgl as lv
import lvgl_esp32
import os
import time

# 添加FPS计数器类
class FPS:
    def __init__(self):
        self.last_time = time.ticks_ms()
        self.fps = 0
        self.frame_count = 0
        self.last_fps = 0  # 添加这行来跟踪上一次的FPS值
    
    def update(self):
        self.frame_count += 1
        current_time = time.ticks_ms()
        if time.ticks_diff(current_time, self.last_time) >= 1000:
            self.last_fps = self.fps  # 保存上一次的值
            self.fps = self.frame_count
            self.frame_count = 0
            self.last_time = current_time
            return True  # 返回True表示FPS值已更新
        return False  # 返回False表示FPS值未更新

wrapper = lvgl_esp32.Wrapper(display,touch,use_spiram=True, buf_lines=48)
#wrapper = lvgl_esp32.Wrapper(display,touch,use_spiram=True, buf_lines=48)
wrapper.init()
os.listdir('/sd')
display.brightness(100)
#顺时转180度
display.swapXY(False)
display.mirrorX(True)
display.mirrorY(True)
touch.swapXY(False)
touch.mirrorX(True)
touch.mirrorY(True)
screen = lv.screen_active()
#screen.set_style_bg_color(lv.color_hex(0x000000), lv.PART.MAIN | lv.STATE.DEFAULT)
#screen.set_style_bg_opa(255, lv.PART.MAIN | lv.STATE.DEFAULT)

screen.set_style_bg_color(lv.color_hex(0x202020), lv.PART.MAIN | lv.STATE.DEFAULT)

# 创建FPS显示标签
fps_label = lv.label(screen)
fps_label.set_style_text_color(lv.color_hex(0x00FF00), 0)  # 绿色文字
fps_label.set_style_text_font(lv.font_montserrat_20, 0)    # 改为20号字体
fps_label.align(lv.ALIGN.TOP_RIGHT, -10, 10)               # 右上角显示

def show_lottie(obj, file_path, w, h, x, y):
    """
    显示 lottie 动画
    :param file_path: json 文件路径
    :param w: 宽度
    :param h: 高度
    :param x: x 偏移
    :param y: y 偏移
    :return: lottie 动画对象
    """
    try:
        with open(file_path, 'r') as file:
            json_data = file.read()
        json_bytes = json_data.encode('utf-8')

        lottie = lv.rlottie_create_from_raw(obj, w, h, json_bytes)
        lottie.align(lv.ALIGN.CENTER, x, y)
        print(lottie)
        return lottie
        
    except Exception as e:
        print(f"Error creating lottie animation: {e}")
        return None

show_lottie(screen, "/rlottie/loading.json",150,150,0,0)

print("启动")
# 创建FPS计数器实例
fps_counter = FPS()

while True:
    lv.timer_handler_run_in_period(5)
    # 只在FPS值更新时才刷新显示
    if fps_counter.update():
        fps_label.set_text(f"FPS: {fps_counter.fps}")





