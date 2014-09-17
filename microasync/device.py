import pyb
from microasync.async import coroutine, SlidingChannel, Delay,\
    ChannelProducer
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
