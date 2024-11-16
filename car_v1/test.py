

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
label = lv.label(screen)
label.set_text(f"MicroPython{os.uname()[2]}")
label.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN)
label.align(lv.ALIGN.CENTER, 0, 0)


def event_handler(event):
    code = event.get_code()
    obj = event.get_target()
    
    print(obj)
    print(code)

lv_ver = lv.label(screen)
lv_ver.set_text(f"LVGL {lv.version_major()}.{lv.version_minor()}.{lv.version_patch()}")
lv_ver.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN)
lv_ver.align_to(label,lv.ALIGN.BOTTOM_MID, 0, -10)




def slider_event_cb(evt):
    slider = evt.get_target_obj()
    display.brightness(slider.get_value())
#
# Create a slider and write its value on a label.
#

# Create a slider in the center of the display
slider = lv.slider(screen)
slider.set_width(200)
slider.set_value(100,True)# Set the width
slider.set_range(20,100)
slider.align_to(label,lv.ALIGN.BOTTOM_MID, 0, 100)
slider.add_event_cb(slider_event_cb, lv.EVENT.VALUE_CHANGED, None) # Assign an event function


a = lv.anim_t()
a.init()
a.set_var(label)
a.set_values(10, 50)
a.set_duration(1000)
a.set_playback_delay(100)
a.set_playback_duration(300)
a.set_repeat_delay(500)
a.set_repeat_count(lv.ANIM_REPEAT_INFINITE)
a.set_path_cb(lv.anim_t.path_ease_in_out)
a.set_custom_exec_cb(lambda _, v: label.set_y(v))
a.start()
print("启动")
while True:
    lv.timer_handler_run_in_period(5)




