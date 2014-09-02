from unittest import TestCase
import core


class ActionTestCase(TestCase):

    def test_can(self):
        action = core.Action(lambda: True, lambda: True)
        self.assertTrue(action.can())

    def test_fail_when_cant_do(self):
        action = core.Action(lambda: False, lambda: True)
        with self.assertRaises(Exception):
            action.do()


class ChannelTestCase(TestCase):

    def test_cant_get_from_empty_channel(self):
        chan = core.Channel()
        action = chan.get()
        self.assertFalse(action.can())

    def test_get_from_channel(self):
        chan = core.Channel()
        action = chan.get()
        chan.put(10).do()
        self.assertTrue(action.can())
        self.assertEqual(action.do(), 10)

    def test_put_to_empty_channel(self):
        chan = core.Channel()
        action = chan.put(10)
        self.assertTrue(action.can())
        action.do()
        self.assertEqual(chan.get().do(), 10)

    def test_cant_put_to_filled_channel(self):
        chan = core.Channel()
        chan.put(10).do()
        self.assertFalse(chan.put(100).can())

    def test_cant_close_closed_channel(self):
        chan = core.Channel()
        chan.close().do()
        self.assertFalse(chan.close().can())

    def test_cant_put_in_closed_channel(self):
        chan = core.Channel()
        chan.close().do()
        self.assertFalse(chan.put(10).can())

    def test_cant_get_from_closed_channel(self):
        chan = core.Channel()
        chan.close().do()
        self.assertFalse(chan.get().can())


class GoBlockTestCase(TestCase):

    def test(self):
        @core.go
        def sum_x_y(x, y):
            return x + y

        @core.go
        def range_10():
            for x in range(10):
                val = yield sum_x_y(x, 10)
                self.assertEqual(val, x + 10)

        range_10()
        core.loop()

    def test_2(self):
        @core.go
        def actor(chan):
            while not chan.is_closed:
                print('get', chan.get(), chan._val)
                x, y = yield chan.get()
                print(x, y)

        chan = core.Channel()

        @core.go
        def sender(chan):
            for x in range(10):
                print('send')
                yield chan.put((x, 2))
            yield chan.close()
        sender(chan)
        actor(chan)
        core.loop()

    def test_go_chan(self):
        @core.go_chan
        def range_(x, y, chan):
            for n in range(x, y):
                yield chan.put(n)

        @core.go
        def actor():
            range_chan = range_(1, 20)
            for _ in range(1, 20):
                print((yield range_chan.get()))

        actor()
        core.loop()
