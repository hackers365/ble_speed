import urequests
import ujson
import lvgl as lv
import time
from hardware import display, touch
import lvgl_esp32
import network
import os
import ntptime

# 常量定义
WIFI_SSID = 'NETGEAR83'
WIFI_PASSWORD = 'ancienthippo982'
CURRENCY_PAIRS = [
    "BTCUSDT",
    "ETHUSDT",
    "SOLUSDT",
    "BNBUSDT",
]

# Initialize LVGL
print("Initializing LVGL...")
wrapper = lvgl_esp32.Wrapper(display, touch)
wrapper.init()
print("LVGL initialized")


def connect_wifi(ssid, password):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print('Connecting to WiFi...')
        wlan.connect(ssid, password)
        while not wlan.isconnected():
            time.sleep(1)
    print('WiFi connected, IP:', wlan.ifconfig()[0])


# 连接到 Wi-Fi
connect_wifi(WIFI_SSID, WIFI_PASSWORD)


# 通过 API 同步时间
def sync_time():
    try:
        response = urequests.get("http://worldtimeapi.org/api/ip")
        time_data = ujson.loads(response.text)
        year, month, day = time_data['datetime'][:10].split('-')
        hour, minute, second = time_data['datetime'][11:19].split(':')

        # 设置 RTC
        import machine
        rtc = machine.RTC()
        rtc.datetime((int(year), int(month), int(day), 0, int(hour), int(minute), int(second), 0))

        print("Time sync successful")
    except Exception as e:
        print("Error syncing time:", str(e))


# 尝试同步时间
sync_time()

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

# 创建时间标签
time_label = lv.label(screen)
time_label.set_style_text_color(lv.color_hex(0xFFFFFF), lv.PART.MAIN)
time_label.set_style_text_font(lv.font_montserrat_20, lv.PART.MAIN)
time_label.align(lv.ALIGN.TOP_MID, 0, 40)

# 创建价格标签
price_labels = {}
for i, pair in enumerate(CURRENCY_PAIRS):
    label = lv.label(screen)
    label.set_style_text_color(lv.color_hex(0xFFFFFF), lv.PART.MAIN)
    label.align(lv.ALIGN.TOP_LEFT, 60, 80 + i * 30)
    price_labels[pair] = label


def fetch_prices():
    symbols = str(CURRENCY_PAIRS).replace("'", '%22')
    symbols = symbols.replace(" ", '')
    url = f"https://api.binance.com/api/v3/ticker/price?symbols={symbols}"
    print("Request URL:", url)
    # url = 'https://api.binance.com/api/v3/ticker/price?symbols=[%22BTCUSDT%22,%22BNBUSDT%22]'
    try:
        response = urequests.get(url)
        print("Response text:", response.text)
        data = ujson.loads(response.text)
        return {item['symbol']: float(item['price']) for item in data}
    except Exception as e:
        print("Error details:", str(e))
        return {}


def update_display(task):
    # 更新时间
    current_time = time.localtime()
    time_str = "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(
        current_time[0], current_time[1], current_time[2],
        current_time[3], current_time[4], current_time[5])
    time_label.set_text(time_str)

    # 更新价格
    prices = fetch_prices()
    if not prices:
        return

    for pair, label in price_labels.items():
        if pair in prices:
            price_text = f"{pair}: ${prices[pair]:.2f}"
        else:
            price_text = f"{pair}: Error"
            price_text = f"{prices}"
        label.set_text(price_text)
        print("Set text to:", price_text)


# 创建定时器更新显示
timer = lv.timer_create(update_display, 1000, None)

print("启动")

# 主循环
while True:
    lv.timer_handler_run_in_period(5)
