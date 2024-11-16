

from hardware import display,touch

import lvgl as lv
import lvgl_esp32
import os
wrapper = lvgl_esp32.Wrapper(display,touch)
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
screen.set_style_bg_color(lv.color_hex(0x000000), lv.PART.MAIN | lv.STATE.DEFAULT)
screen.set_style_bg_opa(255, lv.PART.MAIN | lv.STATE.DEFAULT)


arc = lv.arc(screen)

#arc.set_style_arc_width(20, lv.PART.INDICATOR) #外框宽度
arc.set_style_arc_width(20, lv.PART.MAIN) #底层背景宽度


arc.set_style_bg_opa(lv.OPA.TRANSP, lv.PART.KNOB) #删掉尾巴
arc.set_style_arc_opa(lv.OPA.TRANSP, lv.PART.INDICATOR)


arc.set_style_arc_color(lv.color_hex(0xFF0000), lv.PART.MAIN) #底层颜色
#arc.set_style_arc_color(lv.color_hex(0xffffff), lv.PART.INDICATOR)


#设置颜色
#arc.set_style_arc_color(lv.palette_main(lv.PALETTE.RED), lv.PART.INDICATOR)
#arc.set_style_bg_color(lv.color_hex(0xffffff), lv.PART.MAIN)
#arc.set_style_bg_color(lv.palette_main(lv.PALETTE.RED), lv.PART.MAIN)


#arc.clear_flag(lv.obj.FLAG.CLICKABLE) #不能点击
arc.set_bg_angles(0, 360)   #背景圆环最大角度
arc.set_value(100)          #值，默认0-100
arc.set_size(350,350)       #宽高
arc.center()                #中间
print("启动")
while True:
    lv.timer_handler_run_in_period(5)





