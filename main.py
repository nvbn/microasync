from microasync.csp import loop, go, Delay
from microasync.device import leds, get_switch


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


on_delay()
on_switch()
loop()
