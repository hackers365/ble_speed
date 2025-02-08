import usys as sys
sys.path.append('/common') # See: https://github.com/micropython/micropython/issues/6419
sys.path.append('/rlottie') # See: https://github.com/micropython/micropython/issues/6419

from hardware import display,touch

import fs_driver

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
#screen.set_style_bg_color(lv.color_hex(0x000000), lv.PART.MAIN | lv.STATE.DEFAULT)
#screen.set_style_bg_opa(255, lv.PART.MAIN | lv.STATE.DEFAULT)

screen.set_style_bg_color(lv.color_hex(0x202020), lv.PART.MAIN | lv.STATE.DEFAULT)


#from lv_example_rlottie_approve import lv_example_rlottie_approve

with open('/abc.json', 'r') as file:
    json_data = file.read()
json_bytes = json_data.encode('utf-8')
hex_array = [hex(byte) for byte in json_bytes]

print(type(hex_array))

#lottie = lv.rlottie_create_from_raw(screen, 100, 100, hex_array)
#lottie.center()

#lottie0 = lv.rlottie_create_from_file(screen, 100, 100,"/baby.json")
#lottie0.center()

#lottie6 = lv.rlottie_create_from_file(screen, 120, 120,"baby.json")
#lottie6.center()


print("启动")
while True:
    lv.timer_handler_run_in_period(5)




