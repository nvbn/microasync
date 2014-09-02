import pyb
import core
import time


class Led(object):
    def __init__(self, n):
        self._led = pyb.LED(n)

    @core.go
    def on(self):
        self._led.on()

    @core.go
    def off(self):
        self._led.off()

    @core.go
    def toggle(self):
        self._led.toggle()


class Switch(object):
    def __init__(self):
        self._switch = pyb.Switch()
        self._clicked = False

    @core.go
    def state(self):
        return self._switch()

    def on_clicked(self):
        self._clicked = True

    def reset(self):
        self._clicked = False

    def clicked(self):
        action = core.Action(lambda: self._clicked, self.reset)
        self._switch.callback(self.on_clicked)
        return action


class Timer(object):
    def __init__(self, *args, **kwargs):
        self._timer = pyb.Timer(*args, **kwargs)
        self._subs = 0
        self._ready = False

        def callback(t):
            self._ready = True

        self._timer.callback(callback)

    def when(self):
        self._subs += 1
        return core.Action((lambda: self._ready), self._when_ready)

    def _when_ready(self):
        self._subs -= 1
        if self._subs == 0:
            self._ready = False


def delay(seconds):
    start = time.time()
    return core.Action(lambda: start + seconds < time.time(), lambda: seconds)
