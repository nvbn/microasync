from unittest import TestCase
from time import sleep
from microasync.utils import WithEquality, Promise, Atom
from microasync.async import Channel, SlidingChannel, CoroutineBlock, coroutine, process_all,\
    clone, Delay, ChannelProducer


class WithEqualityTestCase(TestCase):

    def test_same_objects_are_equal(self):
        obj = WithEquality()
        self.assertEqual(obj, obj)

    def test_not_same_objects_not_equal(self):
        first = WithEquality()
        second = WithEquality()
        self.assertNotEqual(first, second)


class PromiseTestCase(TestCase):

    def test_not_delivered_by_default(self):
        prom = Promise()
        self.assertFalse(prom.delivered)
        self.assertIsNone(prom.value)

    def test_delivery(self):
        prom = Promise()
        self.assertTrue(prom.delivery(12))
        self.assertTrue(prom.delivered)
        self.assertEqual(prom.value, 12)

    def test_cant_be_delivered_twice(self):
        prom = Promise()
        self.assertTrue(prom.delivery(12))
        self.assertFalse(prom.delivery(52))
        self.assertEqual(prom.value, 12)


class AtomTestCase(TestCase):

    def test_reset(self):
        atom = Atom()
        self.assertIsNone(atom.value)
        atom.reset(50)
        self.assertEqual(atom.value, 50)

    def test_swap(self):
        atom = Atom(10)
        self.assertEqual(atom.value, 10)
        atom.swap(lambda x: x * 15)
        self.assertEqual(atom.value, 150)


class ChannelTestCase(TestCase):

    def test_put_into_channel(self):
        chan = Channel()
        prom = chan.put(10)
        chan.process()
        self.assertTrue(prom.delivered)
        self.assertTrue(prom.value)
        
    def test_get_from_channel(self):
        chan = Channel()
        prom = chan.get()
        chan.put(52)
        chan.process()
        self.assertTrue(prom.delivered)
        self.assertEqual(prom.value, 52)

    def test_channel_with_limit(self):
        chan = Channel(limit=5)
        put_proms = [chan.put(x) for x in range(5)]
        get_proms = [chan.get() for _ in range(5)]
        for prom in put_proms:
            process_all()
            self.assertTrue(prom.delivered)
            self.assertTrue(prom.value)
        for n, prom in enumerate(get_proms):
            self.assertTrue(prom.delivered)
            self.assertEqual(prom.value, n)


class SlidingChannelTestCase(TestCase):

    def test_channel(self):
        chan = SlidingChannel()
        chan.put(1)
        chan.process()
        chan.put(2)
        chan.process()
        chan.put(3)
        chan.process()
        prom = chan.get()
        chan.process()
        self.assertEqual(prom.value, 3)

    def test_channel_with_limit(self):
        chan = SlidingChannel(limit=5)

        def _and_process(x):
            process_all()
            return x

        put_proms = [_and_process(chan.put(x)) for x in range(10)]
        get_proms = [_and_process(chan.get()) for _ in range(10)]
        for n, prom in enumerate(put_proms):
            process_all()
            self.assertTrue(prom.delivered)
            self.assertTrue(prom.value)
        for n, prom in enumerate(get_proms):
            if n > 4:
                self.assertFalse(prom.delivered)
            else:
                self.assertTrue(prom.delivered)
                self.assertEqual(prom.value, n + 5)


class CoroutineBlockTestCase(TestCase):

    def test_block_parking(self):
        def fnc():
            yield Promise()
            yield Promise()

        block = CoroutineBlock(fnc())
        self.assertFalse(block.parked)
        block.process()
        self.assertTrue(block.parked)
        block._last_promise.delivery(True)
        self.assertFalse(block.parked)

    def test_values_passing_when_generator(self):
        def fnc():
            val = yield Promise()
            self.assertEqual(val, 50)
            return 12

        block = CoroutineBlock(fnc())
        block.process()
        block._last_promise.delivery(50)
        block.process()
        self.assertTrue(block.delivered)
        self.assertEqual(block.value, 12)

    def test_value_passing_when_fnc(self):
        def fnc():
            return 52
        block = CoroutineBlock(fnc())
        block.process()
        self.assertTrue(block.delivered)
        self.assertEqual(block.value, 52)


class CoroutineDecoratorTestCase(TestCase):

    def test_should_work(self):
        @coroutine
        def inc(x):
            return x + 1

        inc_val = inc(10)
        inc_val.process()
        self.assertTrue(inc_val.delivered)

        @coroutine
        def range_fn(y):
            x = 0
            result = [x]
            while x < y:
                x = yield inc(x)
                result.append(x)
            return result

        prom = range_fn(5)
        while not prom.delivered:
            process_all()
        self.assertEqual(prom.value, [0, 1, 2, 3, 4, 5])


class CloneTestCase(TestCase):

    def _assert_should_work(self, channel_type):
        done = Promise()

        @coroutine
        def aux():
            chan = Channel()
            chans = clone(chan, 5, channel_type)
            yield chan.put(10)
            for r_chan in chans:
                self.assertEqual((yield r_chan.get()), 10)
            yield chan.put(22)
            for r_chan in chans:
                self.assertEqual((yield r_chan.get()), 22)
            done.delivery(True)
        aux()
        while not done.delivered:
            process_all()

    def test_with_channel(self):
        self._assert_should_work(Channel)

    def test_with_sliding_channel(self):
        self._assert_should_work(SlidingChannel)


class DelayTestCase(TestCase):

    def test_should_work(self):
        delay = Delay(1)
        sleep(1)
        process_all()
        self.assertTrue(delay.delivered)


class ChanProducerTestCase(TestCase):

    def test_should_work(self):
        chan = Channel()
        producer = ChannelProducer(chan)
        clones = [producer.get_clone() for _ in range(5)]
        chan.put(12)
        process_all()
        for chan_clone in clones:
            prom = chan_clone.get()
            while not prom.delivered:
                process_all()
            self.assertEqual(prom.value, 12)
