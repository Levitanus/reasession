from __future__ import annotations
import typing as ty
import typing_extensions as te
import reapy as rpr

from . import SessionError, HostIP, FreezeState
T1 = ty.TypeVar('T1')


class Project(rpr.Project):
    _host_ip: HostIP

    def __init__(
        self, id: ty.Union[str, int], ip: HostIP = HostIP('localhost')
    ) -> None:
        self._host_ip = ip
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
