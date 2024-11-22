import lvgl_esp32
import  machine,vfs,os
# Adapt these values for your own configuration
spi = lvgl_esp32.QSPI(
    2,
    baudrate=80_000_000,
    sck=9,
    data0=11,
    data1=12,
    data2=13,
    data3=14,
    max_transfer_s=int(360*96*24)
)
spi.init()
print("SPI INITED")
display = lvgl_esp32.Display(
    spi=spi,
    width=360,
    height=360,
    swap_xy=False,
    mirror_x=False,
    mirror_y=False,
    invert=True,
    bgr=True,
    reset=47,
    cs=10,
    blk=15,
    pixel_clock=50_000_000,
)
display.init()

touch=lvgl_esp32.Touch(
    scl=8,
    sda=7,
    rst=40,
    inter=41,
    width=360,
    height=360,
    swap_xy=False,
    mirror_x=False,
    mirror_y=False,
    )
touch.init()

sdcard=machine.SDCard(clk=3,cmd=4,d0=2,d1=1,d2=6,d3=5)
vfs.mount(sdcard,'/sd')
