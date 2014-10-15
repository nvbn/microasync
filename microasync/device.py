import pyb
from microasync.async import coroutine, SlidingChannel, Delay,\
    ChannelProducer, Channel, as_chan
from microasync.utils import Atom

_switch = SlidingChannel()
_switch_producer = ChannelProducer(_switch)


def get_switch():
    return _switch_producer.get_clone()


_switch_atom = Atom(False)


def _switch_handler():
    switch = pyb.Switch()
    switch.callback(lambda: _switch_atom.reset(True))

    @coroutine
    def aux():
        """For preventing MemoryError."""
        while True:
            if _switch_atom.value:
                yield _switch.put(True)
                _switch_atom.reset(False)
            yield Delay(0)
    aux()

_switch_handler()


leds = Channel()


@coroutine
def _leds_handler():
    while True:
        led, action = yield leds.get()
        getattr(pyb.LED(led), action)()
_leds_handler()


servo_chans = {}


def get_servo(num):
    if not num in servo_chans:
        servo_chans[num] = (Channel(), SlidingChannel())
    servo = pyb.Servo(num)

    @coroutine
    def set_aux():
        while True:
            val = yield servo_chans[num][0].get()
            servo.angle(val)
    set_aux()

    @coroutine
    def get_aux():
        while True:
            val = servo.angle()
            yield servo_chans[num][1].put(val)
            yield Delay(0)
    get_aux()
    return servo_chans[num]


accel = SlidingChannel()
accel_run = Atom(False)


def get_accel():
    @coroutine
    def aux():
        dev = pyb.Accel()
        while True:
            yield accel.put(dev.filtered_xyz())
            yield Delay(0)

    if not accel_run.value:
        aux()
    return accel


@as_chan(SlidingChannel)
def get_input_pin(chan, pin_name):
    pin = pyb.Pin(pin_name, mode=pyb.Pin.INP)
    while True:
        yield chan.put(pin.value())
        yield Delay(0)


@as_chan(Channel)
def get_output_pin(chan, pin_name):
    pin = pyb.Pin(pin_name, mode=pyb.Pin.OUT_PP)
    while True:
        value = yield chan.get()
        pin.value(value)
