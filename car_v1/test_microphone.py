import uasyncio as asyncio
from lvgl_esp32 import FFT
import time
#异步任务框架
loop = asyncio.get_event_loop()

#读取麦克风示例
from machine import I2S
from machine import Pin
import ustruct
FFT_N=const(128)
FFT_R=const(16000)
sck_pin = Pin(42)   # Serial clock output
ws_pin = Pin(45)    # Word clock output
sd_pin = Pin(46)    # Serial data output
audio_in = I2S(1,
               sck=sck_pin, ws=ws_pin, sd=sd_pin,
               mode=I2S.RX,
               bits=16,
               format=I2S.MONO,
               rate=FFT_R,
               ibuf=FFT_R*2)
IBUFF_LEN=FFT_N*2
#读取音频数据
async def main():
    fft_plan=FFT(FFT_N,FFT.REAL,FFT.FORWARD)
    sreader = asyncio.StreamReader(audio_in)
    start_ms=time.ticks_ms()
    loop=0
    while loop<100:
        loop+=1
        buf=bytearray(IBUFF_LEN)
        buf_view=memoryview(buf)
        num_read =0
        while num_read<IBUFF_LEN:
            num_read+=await sreader.readinto(buf_view[num_read:])
        samples=ustruct.unpack('<'+'h'*(FFT_N),buf)
        fft_plan.execute(samples)
        #await asyncio.sleep_ms(FFT_R//FFT_N)
    print(f"耗时:{time.ticks_diff(time.ticks_ms(),start_ms)}ms")
    #释放内存
    del fft_plan

if __name__ == '__main__':
    asyncio.create_task(main())
    loop.run_forever()

