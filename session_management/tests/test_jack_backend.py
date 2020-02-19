import unittest as ut
from ..connections import jack_backend as jb
import jack


class TestJackBackend(ut.TestCase):
    def test_init(self) -> None:
        self.back1 = jb.JackBackend(
            'back1', 'jack_load netmanager -i "-a 192.168.2.1 -p 9002"', True
        )
        client1 = jack.Client('testin')
        client2 = jack.Client('testout')

        pin = client1.inports.register('my_in')
        pout = client2.outports.register('my_out')
        client1.activate()
        client2.activate()
        self.back1.force_connect(pout, pin)
        self.back1.force_connect(pout, pin)
