from microasync.utils import Promise, WithEquality
from time import time, sleep


processable = []


class Channel(WithEquality):
    """Channel for communicating between coroutines.

    Usage (should be used only inside coroutine):

    .. code-block:: python

        chan = Channel()
        yield chan.put('test')  # puts 'tests' in channel
        result = yield chan.get()  # gets value from channel
        print(result)  # prints 'test'

    """

    def __init__(self, limit=1):
        """

        :param limit: Limit of object in channel.
        :type limit: int

        """
        super(Channel, self).__init__()
        self._messages = []
        self._get_queue = []
        self._put_queue = []
        self._limit = limit
        self.closed = False
        processable.append(self)
        self.clones = []

    def get(self):
        """Get item from channel.

        :returns: Promise for getting item from channel.
        :rtype: Promise

        """
        prom = Promise()
        self._get_queue.append(prom)
        return prom

    def put(self, val):
        """Put item in channel.

        :returns: Promise for putting item in channel.
        :rtype: Promise

        """
        prom = Promise()
        self._put_queue.append((prom, val))
        return prom

    def _process_get(self):
        """Tries to delivery all promises in `get` queue."""
        for prom in self._get_queue:
            if self.closed:
                prom.delivery(None)
            elif self._messages:
                prom.delivery(self._messages.pop(0))
            else:
                break
            self._get_queue.remove(prom)

    def _try_put(self, val):
        """Tries to put item in queue."""
        if len(self._messages) <= self._limit:
            self._messages.append(val)
            return True
        else:
            return False

    def _process_put(self):
        """Tries to delivery all promises in `put` queue."""
        for prom, val in self._put_queue:
            if self.closed:
                prom.delivery(False)
                self._put_queue.remove((prom, val))
            elif self._try_put(val):
                prom.delivery(True)
                self._put_queue.remove((prom, val))

    def process(self):
        """Process promises in queue. For internal use only!"""
        self._process_put()
        self._process_get()


class SlidingChannel(Channel):
    """Channel in which new items overwrites old."""

    def _try_put(self, val):
        """Puts item in queue and overwrites exists."""
        self._messages.append(val)
        self._messages = self._messages[-self._limit:]
        return True


class CoroutineBlock(Promise):
    """Similar to go-block in core.async. Internal use only!"""

    def __init__(self, gen):
        super(CoroutineBlock, self).__init__()
        self._gen = gen
        self._last_promise = Promise()
        self._last_promise.delivery(None)
        processable.append(self)

    @property
    def parked(self):
        """Returns `True` when block parked."""
        return not self._last_promise.delivered

    def process(self):
        """Process promises returned by coroutine generator."""
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
        """Removes self from list of active coroutine blocks."""
        processable.remove(self)


def coroutine(fnc):
    """Decorator for defining coroutine.

    Usage:

    .. code-block:: python

        @coroutine
        def my_coroutine(x):
            print(x)

        my_coroutine()
        loop()  # corouitnes starts working only after starting main loop

    """
    def wrapper(*args, **kwargs):
        return CoroutineBlock(fnc(*args, **kwargs))
    return wrapper


def process_all():
    """Process all promises. Internal use only!"""
    for item in processable[:]:
        item.process()


def loop():
    """Starts main loop."""
    while True:
        process_all()
        sleep(0.1)


def clone(chan, n, chan_type=SlidingChannel):
    """Creates clones of presented channels.

    Usage:

    .. code-block:: python

        chan_1, chan_2 = clone(chan, 2)

    :param chan: Original channel.
    :type chan: Channel
    :param n: Count of clones.
    :type n: int
    :param chan_type: Type of new channels.
    :type chan_type: type[U]
    :returns: Created channels.
    :rtype: list[U]

    """
    result_chans = [chan_type() for _ in range(n)]

    @coroutine
    def aux():
        while True:
            val = yield chan.get()
            for result_chan in result_chans:
                yield result_chan.put(val)
    aux()
    return result_chans


class Delay(Promise):
    """Channel/Promise with functional similar to time.sleep, but
    non-blocking. Should be used only inside coroutine.

    Use like promise:

    .. code-block:: python

        yield Delay(10)  # wait 10 seconds


    Use like a channel:

    .. code-block:: python

        delay_chan = Delay(10)
        while True:
            yield delay_chan.get()
            print('ok!')  # prints 'ok!' every 10 seconds

    """

    def __init__(self, sec):
        """
        :param sec: Timeout in seconds.
        :type sec: float

        """
        super(Delay, self).__init__()
        self._start = time()
        self._sec = sec
        self.delivered = False
        processable.append(self)

    def process(self):
        """Emulate interface of promises. Internal use only!"""
        self.delivered = self._start + self._sec < time()
        if self.delivered:
            processable.remove(self)

    def get(self):
        """Emulate interface of channels."""
        return Delay(self._sec)


class ChannelProducer(object):
    """Helper for creating channel clones.

    Usage:

    .. code-block:: python

        producer = ChannelProducer(chan)
        chan_1 = producer.get_clone()
        chan_2 = producer.get_clone()

    """

    def __init__(self, chan):
        """
        :param chan: Original channel.
        :type chan: Channel

        """
        self._chan = chan
        self._reserved_clone = chan

    def get_clone(self):
        """Creates a clone of original channel.

        :returns: Created channel.
        :rtype: Channel

        """
        self._reserved_clone, self._chan = clone(self._reserved_clone, 2)
        return self._chan


def select(*chans):
    """Creates a channel with works like fifo for messages from original
    channels. Works like `select` from go or `alts!` from `core.async`.

    Usage:

    .. code-block:: python

        select_chan = select(delay_chan, trigger_chan)
        while True:
            chan, val = yield select_chan.get()
            if chan == delay_chan:
                print('delay')
            else:
                print('trig by ', val)

    :param chans: Channels from which we should get items.
    :type chans: Channel
    :returns: Channel with all `chans` items.
    :rtype: Channel

    """
    chan = Channel()

    @coroutine
    def aux(chan_):
        while True:
            val = yield chan_.get()
            yield chan.put((chan_, val))

    for promise in chans:
        aux(promise)

    return chan


def as_chan(create_chan):
    """Decorator which creates channel and coroutine. Passes channel as a
    first value to coroutine and returns that channel.

    Usage:

    .. code-block:: python

        @as_chan
        def thermo(chan, unit):
            while True:
                yield chan.put(convert(thermo_get(), unit))

        @coroutine
        def main():
            thermo_chan = thermo('C')
            while True:
                print((yield thermo_chan.get()))  # prints current temperature

    :param create_chan: Type of channel.
    :type create_chan: type[Channel]
    :returns: Created coroutine.

    """
    def decorator(fn):
        def wrapped(*args, **kwargs):
            chan = create_chan()
            coroutine(fn)(chan, *args, **kwargs)
            return chan
        return wrapped
    return decorator


def do_all(*chans):
    """Creates new channel with single item from each of `chans` in sequential
    order. Should be used only inside coroutine.

    Usage:

    .. code-block:: python

        led_state, trig_state = yield do_all(led_chan.get(), trig_chan.get())

    :param chans: Channels from which we need to get items.
    :type chans: Channel
    :returns: Channel in which we put values from `chans`.
    :rtype: Channel

    """
    result_chan = Channel()

    @coroutine
    def aux():
        result = []
        for ch in chans:
            result.append((yield ch))
        yield result_chan.put(result)
    aux()
    return result_chan.get()

