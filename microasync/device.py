"""Experimental non-blocking api for pyboard."""
try:
    import pyb
except ImportError:
    class FakePyb(object):
        def __getattr__(self, item):
            return self

        def __call__(self, *args, **kwargs):
            return self

    pyb = FakePyb()  # for generating documentation

from microasync.async import coroutine, SlidingChannel, Delay,\
    ChannelProducer, Channel, as_chan
from microasync.utils import Atom

_switch = SlidingChannel()
_switch_producer = ChannelProducer(_switch)


def get_switch():
    """Creates channel for onboard switch. Should be used only in coroutine.

    Usage:

    .. code-block:: python

        switch = get_switch()
        while True:
            yield switch.get()
            print('clicked!')

    :returns: Channel for onboard switch.
    :rtype: Channel

    """
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

# Coroutine for leds, usage:
# leds.put((1, 'toggle'))  # toggle first led
# leds.put((2, 'off'))  # turn off second led
# leds.put((3, 'on'))  # turn on third led
leds = Channel()


@coroutine
def _leds_handler():
    while True:
        led, action = yield leds.get()
        getattr(pyb.LED(led), action)()
_leds_handler()


servo_chans = {}


def get_servo(num):
    """Creates write and read channels for servo. Should be used
    only in coroutine.

    Usage:

    .. code-block:: python

        servo_set, servo_get = get_servo(1)
        yield servo_set.put(90)  # set servo to 90 degrees
        print((yield servo.get()))  # prints current servo degree

    :param num: Number of servo.
    :type num: int
    :returns: Write and read channels.
    :rtype: (Channel, SlidingChannel)

    """
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
    """Creates channel for on-board accel.

    Usage:

    .. code-block:: python

        accel_chan = get_accel()
        while True:
            print((yield accel_chan.get()))  # prints current accel (x, y, z)

    :returns: Created channel.
    :rtype: Channel

    """
    @coroutine
    def aux():
        dev = pyb.Accel()
        while True:
            yield accel.put(dev.filtered_xyz())
            yield Delay(0)

    if not accel_run.value:
        aux()
    return accel


@as_chan(Channel)
def get_input_pin(chan, pin_name):
    """Creates channel for input pin.

    Usage:

    .. code-block:: python

        pin_chan = get_input_pin('X1')
        yield pin.put(True)  # sets voltage to 3.3V on pin
        yield pin.put(False)  # sets voltage to 0V on pin

    :param pin_name: Name of pin like 'X1'.
    :returns: Created channel.
    :rtype: Channel

    """

    pin = pyb.Pin(pin_name, mode=pyb.Pin.INP)
    while True:
        yield chan.put(pin.value())
        yield Delay(0)


@as_chan(SlidingChannel)
def get_output_pin(chan, pin_name):
    """Creates channel for output pin.

    Usage:

    .. code-block:: python

        pin_chan = get_output_pin('X1')
        print((yield pin_chan.get())  # prints current pin state.

    :param pin_name: Name of pin like 'X1'.
    :returns: Created channel.
    :rtype: SlidingChannel

    """
    pin = pyb.Pin(pin_name, mode=pyb.Pin.OUT_PP)
    while True:
        value = yield chan.get()
        pin.value(value)
