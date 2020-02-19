import unittest as ut
import pickle as pcl
import typing as ty

from .. import networking as ntw


def _example_func() -> str:
    return 'pickled'


class TestHandler(ntw.IHandler):
    def __init__(self, data_type: bytes) -> None:
        self.data_type = data_type

    def can_handle(self, data_type: bytes) -> bool:
        if data_type == self.data_type:
            return True
        return False

    def handle(self, data_type: bytes, data: bytes) -> bytes:
        return data


class TestLittleCase(ut.TestCase):
    def test_encode(self) -> None:
        simple = ntw.encode_data('my_string')
        self.assertEqual(simple, b'my_string')
        with self.assertRaises(AttributeError):
            ntw.encode_data({"a": lambda x: x + 1})  # type:ignore
        pickled = ntw.encode_data({"a": _example_func})
        decoded = ty.cast(
            ty.Dict[str, ty.Callable[[], str]], pcl.loads(pickled)
        )
        self.assertIsInstance(decoded, ty.Dict)
        self.assertEqual(decoded['a'](), 'pickled')
        self.assertEqual(ntw.encode_data(b'stroke'), b'stroke')

    def test_fill_prefix(self) -> None:
        with self.assertRaises(AssertionError) as e:
            ntw._fill_prefix('12345678910')
        self.assertEqual(str(e.exception), 'too long prefix')
        with self.assertRaises(AssertionError) as e:
            ntw._fill_prefix('')
        self.assertEqual(
            str(e.exception), 'no point of making prefix with null string'
        )
        self.assertEqual(ntw._fill_prefix('pref'), b'000000pref')

    def test_ihandler(self) -> None:
        h = ntw.IHandler()
        self.assertEqual(h.handle(b'type', b'data'), b'IHandler passed')
        self.assertFalse(h.can_handle(b'type'))

    def test_SlaveTCPHandler(self) -> None:
        with self.assertRaises(AssertionError) as e:
            ntw.SlaveTCPHandler.register(object())  # type:ignore
        self.assertEqual(str(e.exception), 'accept only instances of IHandler')
        ntw.SlaveTCPHandler.register(ntw.IHandler())
        ntw.SlaveTCPHandler.register(TestHandler(b'test_data'))
