"""Helpers for internal use only!"""
try:
    import pyb
except ImportError:
    class pyb(object):
        _counter = 0

        @classmethod
        def rng(cls):
            try:
                return cls._counter
            finally:
                cls._counter += 1


class WithEquality(object):
    """Class for avoiding micropython limitations with objects equality."""

    def __init__(self):
        self._id = pyb.rng()

    def __eq__(self, other):
        return isinstance(other, WithEquality) and self._id == other._id


class Promise(WithEquality):

    def __init__(self):
        super(Promise, self).__init__()
        self.delivered = False
        self.value = None

    def delivery(self, value):
        if self.delivered:
            return False
        else:
            self.value = value
            self.delivered = True
            return True


class Atom(WithEquality):

    def __init__(self, value=None):
        super(Atom, self).__init__()
        self.reset(value)

    def reset(self, value):
        self.value = value

    def swap(self, fn):
        self.reset(fn(self.value))
