from microasync.device import get_servo, get_accel, get_switch
from microasync.async import coroutine, loop, Delay, select


@coroutine
def servo_coroutine():
    servo, _ = get_servo(1)
    accel = get_accel()
    switch = get_switch()
    on = False
    x = 0
    accel_or_switch = select(switch, accel)
    while True:
        chan, val = yield accel_or_switch.get()
        if chan == accel:
            x, *_ = val
        elif chan == switch:
            on = not on

        if on:
            yield servo.put(x)
        yield Delay(0)


servo_coroutine()
loop()
