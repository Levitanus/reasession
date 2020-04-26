from reasession.session import misc
import reapy as rpr
import pytest as pt
import typing as ty

T1 = ty.TypeVar('T1')


def test_cashed_property() -> None:

    class MyProp:

        def __init__(self) -> None:
            self.values: ty.Dict[int, ty.Dict[str, object]] = {}
            self.n_calls = 0

        def __get__(self, obj: T1, cls: ty.Type[T1]) -> ty.Dict[str, object]:
            self.n_calls += 1
            return self.values[id(obj)]

        def __set__(self, obj: T1, value: ty.Dict[str, object]) -> None:
            self.n_calls += 1
            self.values[id(obj)] = value

    class Simple:

        def __init__(self, prop: ty.Dict[str, object]) -> None:
            self.my_prop: MyProp = prop

        my_prop = MyProp()

        sample = misc.CashedProperty('my_prop')

        @sample
        def method(self, arg: int, my_prop: ty.Dict[str, object]) -> int:
            return arg
