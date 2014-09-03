from microasync.csp import loop, go, Delay
from microasync.device import leds, get_switch, get_timer_counter


@go
def on_delay():
    while True:
        for led in range(1, 5):
            yield leds.put((led, 'toggle'))
            yield Delay(1)


@go
def on_switch():
    switch = get_switch()
    while True:
        for led in range(1, 5):
            yield switch.get()
            yield leds.put((led, 'off'))


@go
def on_timer_counter():
    counter = get_timer_counter(2, prescaler=83, period=0x3fffffff)
    while True:
        val = yield counter.get()
        print(val)
        yield Delay(1)


on_delay()
on_switch()
on_timer_counter()
loop()
