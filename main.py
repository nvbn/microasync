from microasync.async import loop, coroutine, Delay
from microasync.device import leds, get_switch, get_servo


@coroutine
def on_delay():
    while True:
        for led in range(1, 5):
            yield leds.put((led, 'toggle'))
            yield Delay(1)


@coroutine
def on_switch():
    switch = get_switch()
    while True:
        for led in range(1, 5):
            yield switch.get()
            yield leds.put((led, 'off'))


@coroutine
def servo_rotator():
    s_set, s_get = get_servo(1)
    while True:
        for angle in list(range(-90, 90, 5)) + list(range(90, -90, -5)):
            yield s_set.put(angle)
            val = yield s_get.get()
            print(val)


on_delay()
on_switch()
servo_rotator()
loop()
