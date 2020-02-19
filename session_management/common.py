import typing as ty
import typing_extensions as te
import reapy as rpr
from enum import Enum

FuncType = ty.Callable[..., ty.Any]
F = ty.TypeVar('F', bound=FuncType)
T = ty.TypeVar('T')


@te.runtime_checkable
class Stringable(te.Protocol):
    def __str__(self) -> str:
        pass


class Log:
    """Reascript logger."""
    _console = False
    _print = False

    @classmethod
    def __call__(cls, *args: Stringable, sep: str = ' ') -> None:
        line = sep.join([str(i) for i in args])
        if cls._console:
            if rpr.is_inside_reaper():
                rpr.defer(rpr.print, line)
            else:
                rpr.print(line)
        if cls._print:
            print(line)

    @classmethod
    def enable_console(cls) -> None:
        """Make log() calls produce output to reaper console."""
        cls._console = True

    @classmethod
    def enable_print(cls) -> None:
        """Make log() calls produce output to command line."""
        cls._print = True


log = Log()


class TimeCallback:
    """Can be used to make periodic calls from defer loop."""
    def __init__(
        self,
        callback: ty.Callable[[], None],
        time: float = 1,
        run_immediately: bool = True
    ) -> None:
        self._treshold = int(time * 30)
        if run_immediately:
            self._count = self._treshold
        else:
            self._count = 0
        self._callback = callback

    def run(self) -> None:
        """Callback to be placed in defer loop."""
        if self._count >= self._treshold - 1:
            self._callback()
            self._count = 0
            return
        self._count += 1


class PropertyCallback(ty.Generic[T]):
    def __init__(
        self,
        tracked_api: ty.Callable[[], T],
        callback: ty.Callable[[], None],
        tracking_interval: ty.Optional[float] = None,
    ) -> None:
        self._check_func = tracked_api
        self._cashed_result = tracked_api()
        self._user_callback = callback
        if tracking_interval:
            timer = TimeCallback(
                self._callback, time=tracking_interval, run_immediately=False
            )
            setattr(self, 'run', timer.run)

    def _callback(self) -> None:
        new = self._check_func()
        print(self._cashed_result, new)
        if new != self._cashed_result:
            self._cashed_result = new
            self._user_callback()

    def run(self) -> None:
        self._callback()

    @property
    def value(self) -> T:
        return self._cashed_result


def is_stopped() -> bool:
    return rpr.Project().play_state not in ('play, record')


class SolarizedPallete(Enum):
    base03 = 0x002b36
    base02 = 0x07362
    base01 = 0x586e75
    base00 = 0x657b83
    base0 = 0x839496
    base1 = 0x93a1a1
    base2 = 0xeee8d5
    base3 = 0xfdf6e3
    yellow = 0xb58900
    orange = 0xcb4b16
    red = 0xdc322f
    magenta = 0xd33682
    violet = 0x6c71c4
    blue = 0x268bd2
    cyan = 0x2aa198
    green = 0x859900
