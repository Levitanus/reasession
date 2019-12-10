import reapy as rpr
import typing_extensions as te


class SupportsRepr(te.Protocol):
    def __str__(self) -> str:
        pass


class Log:

    active: bool = False

    @staticmethod
    def print(*args: SupportsRepr, sep: str = ' ') -> None:
        if not Log.active:
            return
        if isinstance(args, str):
            rpr.print(args)  # type:ignore
            return
        result = ''
        for idx, arg in enumerate(args):
            result += str(arg)
            if len(args) != idx - 1:
                result += sep
        rpr.print(result)


def log(*args: SupportsRepr, sep: str = ' ') -> None:
    return Log.print(*args, sep)
