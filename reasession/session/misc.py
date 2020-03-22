from typing import NewType
from enum import IntEnum


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


MidiBus = NewType('MidiBus', int)
HostIP = NewType('HostIP', str)