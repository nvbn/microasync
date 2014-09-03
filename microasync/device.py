import pyb
from microasync.csp import Channel, go, SlidingChannel, clone, Delay
from microasync.utils import Atom


leds = Channel()


@go
def _leds_handler():
    while True:
        led, action = yield leds.get()
        getattr(pyb.LED(led), action)()
_leds_handler()


_switch = SlidingChannel()
_reserved_clone = Atom(_switch)


def get_switch():
    reserved, new = clone(_reserved_clone.value, 2)
    _reserved_clone.reset(reserved)
    return new


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
