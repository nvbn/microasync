import pyb


class EQ(object):
    def __init__(self):
        self._id = pyb.rng()

    def __eq__(self, other):
        return isinstance(other, EQ) and self._id == other._id


class Action(EQ):
    def __init__(self, can, do, name=''):
        super(Action, self).__init__()
        self.can = can
        self._do = do
        self.name = name

    def do(self):
        if not self.can():
            raise Exception()
        return self._do()

    def __repr__(self):
        return '<Action: {}>'.format(self.name)


class Some(object):
    def __init__(self, val):
        self.val = val


class _Nothing(object):
    pass


nothing = _Nothing()


class Channel(object):

    def __init__(self, name=''):
        self._val = nothing
        self.is_closed = False
        self.name = name

    def put(self, val):
        def _can_put():
            return self._val is nothing and not self.is_closed

        def _do_put():
            self._val = Some(val)

        return Action(_can_put, _do_put, 'Put {} in {}'.format(val, self))

    def get(self):
        def _can_get():
            return self._val is not nothing and not self.is_closed

        def _do_get():
            val = self._val.val
            self._val = nothing
            return val

        return Action(_can_get, _do_get, 'Get from {}'.format(self))

    def close(self):
        def _can_close():
            return not self.is_closed

        def _do_close():
            self.is_closed = True

        return Action(_can_close, _do_close, 'Close {}'.format(self))

    def __repr__(self):
        return '<Channel: {}>'.format(self.name)


class SlidingChannel(Channel):

    def put(self, val):
        def _can_put():
            return not self.is_closed

        def _do_put():
            self._val = Some(val)

        return Action(_can_put, _do_put, 'Put {} in {}'.format(val, self))


class GoBlock(EQ):
    def __init__(self, gen, name=''):
        super(GoBlock, self).__init__()
        self.chan = Channel(name)
        self.gen = gen
        self.val = None
        self.name = name
        self.parked = False

    def send(self):
        return self.gen.send(self.val)

    def __repr__(self):
        return '<GoBlock: {}>'.format(self.name)


blocks = []
actions = []


def go(fnc):
    def block(*args, **kwargs):
        go_block = GoBlock(
            fnc(*args, **kwargs),
            '{} with {} and {}'.format(fnc, args, kwargs))
        blocks.append(go_block)
        return go_block.chan.get()
    return block


def go_chan(fnc):
    def wrapped(*args, **kwargs):
        chan = Channel()
        go(fnc)(*args, chan=chan, **kwargs)
        return chan
    return wrapped


def bind(action, block):
    action.block = block
    return action


def loop():
    while blocks:
        for block in blocks:
            if block.parked:
                continue

            try:
                action = block.send()
            except StopIteration as e:
                action = block.chan.put(e.value)
                blocks.remove(block)
            except AttributeError as e:
                action = block.chan.put(block.gen)
                blocks.remove(block)
            actions.append(bind(action, block))
            block.parked = True

        for action in actions:
            if action.can():
                action.block.val = action.do()
                actions.remove(action)
                action.block.parked = False
