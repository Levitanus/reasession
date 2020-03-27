import typing as ty
from enum import IntEnum
T1 = ty.TypeVar('T1')
FuncType = ty.Callable[..., ty.Any]  # type:ignore
FT = ty.TypeVar('FT', bound=FuncType)


class SessionError(Exception):
    pass


class FreezeState(IntEnum):
    """Represents Project or Track Instruments state.

    Attributes
    ----------
    disabled : int
    freezed : int
    offline : int
    online : int
    """

    online = 0
    offline = 1
    disabled = 2
    freezed = 3


MidiBus = ty.NewType('MidiBus', int)
HostIP = ty.NewType('HostIP', str)


class CashedProperty:

    def __init__(self, prop_name: str) -> None:
        self.prop_name = prop_name

    def __get__(self, obj: T1, cls: ty.Type[T1]) -> ty.Callable[[FT], FT]:
        return self.__call__

    def __call__(self, func: FT) -> FT:
        ...
