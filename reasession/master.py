import reapy as rpr
from reapy import reascript_api as RPR
from common import TimeCallback


class Master:
    def run(self) -> None:
        ...

    def at_exit(self) -> None:
        ...
