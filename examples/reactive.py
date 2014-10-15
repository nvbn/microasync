from microasync.async import coroutine, as_chan, Channel, do_all, select
from microasync.device import get_switch, get_output_pin


@as_chan(Channel)
def get_3_led(chan, left, right):
    left_pin = get_output_pin(left)
    right_pin = get_output_pin(right)
    while True:
        msg = yield chan.get()
        print(msg)
        if msg == 'red':
            yield do_all(left_pin.put(1),
                         right_pin.put(0))
        elif msg == 'green':
            yield do_all(left_pin.put(0),
                         right_pin.put(1))
        elif msg == 'yellow':
            yield do_all(left_pin.put(1),
                         right_pin.put(1))
        elif msg == 'none':
            yield do_all(left_pin.put(0),
                         right_pin.put(0))


@as_chan(Channel)
def switchable_filter(chan, orig_chan, fn):
    select_ch = select(get_switch(), chan)
    enabled = False
    while True:
        result_ch, val = yield select_ch.get()
        if result_ch == chan:
            if not enabled or fn(val):
                yield orig_chan.put(val)
        else:
            enabled = not enabled


@coroutine
def main():
    leds = (switchable_filter(get_3_led('X1', 'X2'), lambda msg: msg != 'red'),
            switchable_filter(get_3_led('X3', 'X4'), lambda msg: msg == 'red'))
    while True:
        for led in leds:
            for mode in ('red', 'green', 'yellow', 'none'):
                yield led.put(mode)
