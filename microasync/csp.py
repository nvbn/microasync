from microasync.utils import Promise, WithEquality
from time import time, sleep


channels = []
blocks = []


class Channel(WithEquality):

    def __init__(self, limit=1):
        super(Channel, self).__init__()
        self._messages = []
        self._get_queue = []
        self._put_queue = []
        self._limit = limit
        self.closed = False
        channels.append(self)
        self.clones = []

    def get(self):
        prom = Promise()
        self._get_queue.append(prom)
        return prom

    def put(self, val):
        prom = Promise()
        self._put_queue.append((prom, val))
        return prom

    def _process_get(self):
        for prom in self._get_queue:
            if self.closed:
                prom.delivery(None)
            elif self._messages:
                prom.delivery(self._messages.pop(0))
            else:
                break
            self._get_queue.remove(prom)

    def _try_put(self, val):
        if len(self._messages) <= self._limit:
            self._messages.append(val)
            return True
        else:
            return False

    def _process_put(self):
        for prom, val in self._put_queue:
            if self.closed:
                prom.delivery(False)
                self._put_queue.remove((prom, val))
            elif self._try_put(val):
                prom.delivery(True)
                self._put_queue.remove((prom, val))

    def process(self):
        self._process_put()
        self._process_get()


class SlidingChannel(Channel):

    def _try_put(self, val):
        self._messages.append(val)
        self._messages = self._messages[-self._limit:]
        return True


class GoBlock(Promise):
    def __init__(self, gen):
        super(GoBlock, self).__init__()
        self._gen = gen
        self._last_promise = Promise()
        self._last_promise.delivery(None)
        blocks.append(self)

    @property
    def parked(self):
        return not self._last_promise.delivered

    def process(self):
        if not self.parked:
            try:
                self._last_promise = self._gen.send(self._last_promise.value)
            except StopIteration as e:
                self.delivery(e.value)
                self._close()
            except AttributeError:
                self.delivery(self._gen)
                self._close()

    def _close(self):
        blocks.remove(self)


def go(fnc):
    def wrapper(*args, **kwargs):
        return GoBlock(fnc(*args, **kwargs))
    return wrapper


def process_all():
    for channel in channels:
        channel.process()
    for block in blocks:
        block.process()


def loop():
    while True:
        process_all()
        sleep(0.1)


def clone(chan, n, chan_type=SlidingChannel):
    result_chans = [chan_type() for _ in range(n)]

    @go
    def aux():
        while True:
            val = yield chan.get()
            for result_chan in result_chans:
                yield result_chan.put(val)
    aux()
    return result_chans


class Delay(Promise):

    def __init__(self, sec):
        super(Delay, self).__init__()
        self._start = time()
        self._sec = sec
        self.delivered = False
        blocks.append(self)

    def process(self):
        self.delivered = self._start + self._sec < time()
        if self.delivered:
            blocks.remove(self)
