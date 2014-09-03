import pyb
from microasync.csp import go, SlidingChannel, Delay,\
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


# from https://github.com/mithru/MicropythonLibs/blob/master/Ultrasonic/module/ultrasonic.py
class Ultrasonic(object):
    def __init__(self, tPin, ePin):
        print('@@@@')
        self.triggerPin = tPin
        self.echoPin = ePin

        # Init trigger pin (out)
        self.trigger = pyb.Pin(self.triggerPin)
        self.trigger.init(pyb.Pin.OUT_PP, pyb.Pin.PULL_NONE)
        self.trigger.low()

        # Init echo pin (in)
        self.echo = pyb.Pin(self.echoPin)
        self.echo.init(pyb.Pin.IN, pyb.Pin.PULL_NONE)

    @go
    def distance_in_inches(self):
        dist = yield self.distance_in_cm()
        return dist * 0.3937

    @go
    def distance_in_cm(self):
        start = 0
        end = 0

        # Create a microseconds counter.
        micros = pyb.Timer(2, prescaler=83, period=0x3fffffff)
        micros.counter(0)

        # Send a 10us pulse.
        self.trigger.high()
        pyb.udelay(10)
        self.trigger.low()

        # Wait 'till whe pulse starts.
        while self.echo.value() == 0:
            print(self.echo.value())
            start = micros.counter()
            yield Delay(0)

        # Wait 'till the pulse is gone.
        while self.echo.value() == 1:
            print(self.echo.value())
            end = micros.counter()
            yield Delay(0)

        # Deinit the microseconds counter
        micros.deinit()

        # Calc the duration of the recieved pulse, divide the result by
        # 2 (round-trip) and divide it by 29 (the speed of sound is
        # 340 m/s and that is 29 us/cm).
        dist_in_cm = ((end - start) / 2) / 29

        return dist_in_cm
