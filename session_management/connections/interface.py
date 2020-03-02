from abc import ABCMeta, abstractmethod
from enum import IntEnum
import typing as ty
import typing_extensions as te
import IPy
import reapy as rpr
import warnings


class ConnectionsError(Exception):
    pass


class PartiallyConnected(ConnectionsError):
    def __init__(
        self,
        missing: ty.List['Connection'],
        error_string: str = 'Partially established connections! Missed: {miss}'
    ):
        self.missing_connectnions = missing
        super().__init__(error_string.format(miss=missing))


class SlaveTrack(te.TypedDict):
    host: str
    track: rpr.Track


class OutTrack(te.TypedDict):
    track: rpr.Track
    slave: SlaveTrack


class HostInfo(te.TypedDict):
    host: str
    in_tracks: ty.List[rpr.Track]
    out_tracks: ty.List[OutTrack]


class Connector(ABCMeta):
    def __init__(self, hosts: ty.List[HostInfo]) -> None:
        self._hosts = hosts

    def update(self, hosts: ty.List[HostInfo]) -> None:
        self._hosts = hosts
        self.connect_all()

    @abstractmethod
    def connect_all(self) -> None:
        ...
