#
# Command line for running this example on the unix port from examples directory:
# MICROPYPATH=./:../lib ../../../ports/unix/micropython -i Dynamic_loading_font_example.py
#

import usys as sys
sys.path.append('') # See: https://github.com/micropython/micropython/issues/6419

try:
    script_path = __file__[:__file__.rfind('/')] if __file__.find('/') >= 0 else '.'
except NameError:
    script_path = ''

import fs_driver

from hardware import display,touch

import lvgl as lv
import lvgl_esp32

wrapper = lvgl_esp32.Wrapper(display,touch)
wrapper.init()

# 设置显示
display.brightness(100)
display.swapXY(False)
display.mirrorX(True)
display.mirrorY(True)
touch.swapXY(False)
touch.mirrorX(True)
touch.mirrorY(True)

# 创建屏幕和设置背景
screen = lv.screen_active()
screen.set_style_bg_color(lv.color_hex(0x000000), lv.PART.MAIN | lv.STATE.DEFAULT)
screen.set_style_bg_opa(255, lv.PART.MAIN | lv.STATE.DEFAULT)

# FS driver init.

fs_drv = lv.fs_drv_t()
fs_driver.fs_register(fs_drv, 'S')

'''
　load the font file from filesystem(For me is flash )
　How to convert font files refer here: https://github.com/lvgl/lv_font_conv
　font-PHT-en-20.bin:
　　　lv_font_conv --size 20 --format bin --bpp 1 --font Alibaba-PuHuiTi-Medium.subset.ttf --range 0x20-0x7f --no-compress -o font-PHT-en-20.bin
　font-PHT-cn-20.bin:
　　　lv_font_conv --size 20 --format bin --bpp 1 --font Alibaba-PuHuiTi-Medium.subset.ttf --range 0x4e00-0x4e56　--no-compress　-o font-PHT-cn-20.bin
　font-PHT-jp-20.bin:
　　　lv_font_conv --size 20 --format bin --bpp 1 --font Alibaba-PuHuiTi-Medium.subset.ttf --range 0x3042-0x3093　--no-compress　-o font-PHT-jp-20.bin
'''

myfont_en = lv.binfont_create("S:%s/font/speed_num_consolas_150.bin" % script_path)
#myfont_en = lv.font_load("S:%s/font/speed_num_test.bin" % script_path)

# 创建样式
style = lv.style_t()
style.init()

style.set_text_font(myfont_en)  # 设置字体
#style.set_text_letter_space(30)
#style.set_text_line_space(10)  # 设置行间距为10像素

label2 = lv.label(screen)
label2.add_style(style, lv.PART.MAIN)
#label2.set_style_text_font(myfont_en, 0)  # set the font
label2.set_text("125")
label2.align(lv.ALIGN.CENTER, 0, 0)
label2.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN)

i = 100
def update_display(task):
    global i
    label2.set_text(str(i))
    i = i + 1


# 创建定时器更新显示
timer = lv.timer_create(update_display, 500, None)

# 主循环
while True:
    lv.timer_handler_run_in_period(5)