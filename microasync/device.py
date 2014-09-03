import pyb
from microasync.csp import Channel, go, SlidingChannel, Delay,\
    ChannelProducer
from microasync.utils import Atom


leds = Channel()


@go
def _leds_handler():
    while True:
        led, action = yield leds.get()
        getattr(pyb.LED(led), action)()
_leds_handler()


_switch = SlidingChannel()
_switch_producer = ChannelProducer(_switch)


def get_switch():
    return _switch_producer.get_clone()


_switch_atom = Atom(False)


def _switch_handler():
    switch = pyb.Switch()
    switch.callback(lambda: _switch_atom.reset(True))

    @go
    def aux():
        """For preventing MemoryError."""
        while True:
            if _switch_atom.value:
                yield _switch.put(True)
                _switch_atom.reset(False)
            yield Delay(0)
    aux()

_switch_handler()


_timers = {}


def get_timer_counter(*args, **kwargs):
    chan = SlidingChannel()
    timer = pyb.Timer(*args, **kwargs)

    @go
    def aux():
        while True:
            yield chan.put(timer.counter())
            yield Delay(0)
    aux()
    return chan
