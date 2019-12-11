import typing_extensions as te
import reapy as rpr


class Stringable(te.Protocol):
    def __str__(self) -> str:
        pass


class Log:
    _console = False
    _print = False

    @classmethod
    def __call__(cls, *args: Stringable, sep: str = ' ') -> None:
        line = sep.join([str(i) for i in args])
        if cls._console:
            rpr.defer(rpr.print, line)
        if cls._print:
            print(line)

    @classmethod
    def enable_console(cls) -> None:
        cls._console = True

    @classmethod
    def enable_print(cls) -> None:
        cls._print = True


log = Log()
