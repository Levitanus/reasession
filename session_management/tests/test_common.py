import unittest as ut
import typing as ty

from ..common import Stringable
from ..common import TimeCallback
from ..common import PropertyCallback


class CommonTestCase(ut.TestCase):
    def setUp(self) -> None:
        self.i = 0

    def __init__(self, *args: object, **kwargs: object) -> None:
        self.running = True
        self.runs = 0
        self.called = 0
        self.i = 0
        super().__init__(*args, **kwargs)  # type:ignore

    def _imitate_defer(
        self, func: ty.Callable[[], None], runs: ty.Optional[int] = None
    ) -> None:
        self.running = True
        self.runs = 0
        while self.running:
            self.runs += 1
            func()
            if runs and self.runs == runs:
                self.running = False

    def _simple_callback(self) -> None:
        print('run', self.runs)
        self.called = self.runs

    def test_stringable(self) -> None:
        class MyStringable:
            def __str__(self) -> str:
                return 'string repr'

        obj = MyStringable()
        self.assertIsInstance(obj, Stringable)

    def test_timer_callback(self) -> None:
        timer = TimeCallback(self._simple_callback, run_immediately=True)
        self._imitate_defer(timer.run, runs=1)
        self.assertEqual(self.called, self.runs)
        self.assertEqual(self.runs, 1)
        self._imitate_defer(timer.run, runs=30)
        self.assertEqual(self.called, self.runs)
        self.assertEqual(self.runs, 30)

    def test_property_callback(self) -> None:
        def test_api() -> str:
            self.i += 1
            if self.i < 10:
                return 'not yet'
            else:
                return 'already'

        prop = PropertyCallback(test_api, self._simple_callback)
        self._imitate_defer(prop.run, runs=9)
        self.assertEqual(self.runs, self.called)
        self.assertEqual(prop.value, 'already')

        self.i = 8
        prop2 = PropertyCallback(
            test_api, self._simple_callback, tracking_interval=0.5
        )
        self.assertEqual(prop2.value, 'not yet')
        self._imitate_defer(prop2.run, runs=15)
        self.assertEqual(self.runs, self.called)
        self.assertEqual(prop2.value, 'already')
