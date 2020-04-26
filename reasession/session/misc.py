import typing as ty
from enum import IntEnum
T1 = ty.TypeVar('T1')
FuncType = ty.Callable[..., ty.Any]  # type:ignore
FT = ty.TypeVar('FT', bound=FuncType)


class SessionError(Exception):
    pass


class SlaveUnacessible(SessionError):
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


def lua_kv_formatter(k: ty.Union[int, str], v: ty.Union[float, str]) -> str:
    """Make string from arg and value to send as table to lua script."""
    if isinstance(k, int):
        k += 1
    k, v = map(
        lambda i: f'{i}' if isinstance(i, (float, int)) else f'"{i}"', (k, v)
    )
    return f'[{k}]={v}'


def lua_table_formatter(gen: ty.Iterator[str]) -> str:
    """Join formated members to one lua table as string."""
    return f'{{{",".join(gen)}}}'
