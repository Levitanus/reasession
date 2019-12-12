import typing as ty
import typing_extensions as te
import reapy as rpr


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
        if self._count >= self._treshold:
            self._callback()
            self._count = 0
            return
        self._count += 1
