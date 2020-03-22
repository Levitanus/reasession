from __future__ import annotations
from types import TracebackType
from builtins import BaseException
import typing as ty
import typing_extensions as te
import reapy as rpr
from contextlib import contextmanager, ContextDecorator

from . import SessionError, HostIP, FreezeState
T1 = ty.TypeVar('T1')
FuncType = ty.Callable[..., ty.Any]
FT = ty.TypeVar('FT', bound=FuncType)


class Host:
    _connect: ty.ContextManager[rpr.connect]
    _ir: ty.ContextManager[None]

    def __init__(self, ip: HostIP) -> None:
        with rpr.connect(ip):
            self.ip = ip

    def __call__(self, func: FT) -> FT:
        with self:
            return func

    def __enter__(self) -> Host:
        self._connect = rpr.connect(self.ip)
        self._connect.__enter__()
        self._ir = rpr.inside_reaper()
        self._ir.__enter__()
        return self

    def __exit__(
        self, exc_type: ty.Optional[ty.Type[BaseException]],
        value: ty.Optional[BaseException],
        traceback: ty.Optional[TracebackType]
    ) -> None:
        self._ir.__exit__(exc_type, value, traceback)
        self._connect.__exit__(exc_type, value, traceback)


class Project(rpr.Project):
    _host_ip: HostIP
    _host: ty.Optional[Host]

    def __init__(
        self, id: ty.Union[str, int], ip: HostIP = HostIP('localhost')
    ) -> None:
        self._host_ip = ip
        self._host = None
        super().__init__(id)

    @property
    def last_ip(self) -> HostIP:
        return self._host_ip

    @last_ip.setter
    def last_ip(self, ip: HostIP) -> None:
        self._host_ip = ip


class SlaveProject(Project):
    dirty: bool
    # master_track: rpr.Track
    # subproject: SlaveSubProject
    # acessible: bool
    # last_ip: HostIP

    # master_out_tracks: ty.Dict[MasterOutTrack.ID, MasterOutTrack]
    # slave_in_tracks: ty.Dict[SlaveInTrack.ID, SlaveInTrack]
    # freezed: bool
    # disabled: bool
    # unloaded: bool

    # def __init__(self, id: ty.Union[int, str], host: HostIP) -> None:
    #     super().__init__(id)
    #     self.last_ip = host

    # @property
    # def _args(self) -> ty.Tuple[str, HostIP]:
    #     original = super()._args
    #     return (*original, self.last_ip)
