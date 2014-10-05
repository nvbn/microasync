from microasync.async import loop, coroutine, Delay
import pyb


@coroutine
def toggle_led_on_interval(led, interval):
    while True:
        pyb.LED(led).toggle()
        yield Delay(interval)


toggle_led_on_interval(1, 1)
toggle_led_on_interval(2, 2)
toggle_led_on_interval(3, 1)
toggle_led_on_interval(4, 2)
loop()
