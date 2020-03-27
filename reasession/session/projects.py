from __future__ import annotations
from types import TracebackType
from builtins import BaseException
import typing as ty
import typing_extensions as te
import reapy as rpr
from contextlib import contextmanager

import reasession as rs

from . import SessionError, HostIP, FreezeState
from ..config import EXT_SECTION, MASTER_KEY

FuncType = ty.Callable[..., ty.Any]  # type:ignore
FT = ty.TypeVar('FT', bound=FuncType)


class Host:
    """Represents active REAPER host.

    Note
    ----
    Can be used as contextmanager as well as context decorator.

    Raises
    ------
    reapy.errors.DisabledDistApiError
        if host is unreacheble

    Attributes
    ----------
    ip : HostIP
    """

    _connect: ty.ContextManager[rpr.connect]
    _ir: ty.ContextManager[None]

    def __init__(self, ip: HostIP) -> None:
        with rpr.connect(ip):
            self.ip = ip

    def __call__(self, func: FT) -> FT:
        """Wrap function with self context."""

        def wrapper(*args, **kwargs):  # type:ignore
            with self:
                return func(*args, **kwargs)

        return wrapper  # type:ignore

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

    def __hash__(self) -> int:
        return hash(self.ip)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Host):
            return False
        if other.ip == self.ip:
            return True
        return False


class Project(rpr.Project):
    _host_ip: HostIP
    _host: ty.Optional[Host]
    _slave_projects: ty.Dict[rs.session.Track.ID, SlaveProject]
    _out_tracks: ty.Dict[rs.session.Track.ID, rs.session.Track]

    def __init__(
        self, id: ty.Union[str, int], ip: HostIP = HostIP('localhost')
    ) -> None:
        self._host_ip = ip
        self._host = None
        self._slave_projects = {}
        self._out_tracks = {}
        super().__init__(id)

    @property
    def host(self) -> Host:
        """Project's host.

        :type: Host

        Raises
        ------
        reapy.DisabledDistApiError
            if host is unreacheble
        """
        if self._host:
            return self._host
        return Host(self._host_ip)

    @host.setter
    def host(self, host: Host) -> None:
        self._host = host

    @property
    def last_ip(self) -> HostIP:
        if self._host:
            self._host_ip == self._host.ip
        return self._host_ip

    @contextmanager
    def make_current_project_2(self) -> ty.Iterator[None]:
        """More powerful than just make_current_project.

        Returns
        -------
        ContextManager[None]
            connect to project host and run inside_reaper
        """
        if self._host:
            with self.host:
                with self.make_current_project():
                    yield None
        else:
            with self.make_current_project():
                yield None

    @property
    def is_master(self) -> bool:
        """Whether the project is marked as Master.

        :type: bool
        """
        if self.get_ext_state(EXT_SECTION, MASTER_KEY):
            return True
        return False

    @is_master.setter
    def is_master(self, master: bool) -> None:
        self.set_ext_state(
            EXT_SECTION, MASTER_KEY, 'True' if master is True else ''
        )


class SlaveProject(Project):
    dirty: bool
    master_track: rs.Track
    # subproject: SlaveSubProject

    # master_out_tracks: ty.Dict[MasterOutrs.Track.ID, MasterOutrs.Track]
    # slave_in_tracks: ty.Dict[SlaveInrs.Track.ID, SlaveInrs.Track]
    # freezed: bool
    # disabled: bool
    # unloaded: bool

    @property
    def is_accessible(self) -> bool:
        try:
            with self.host:
                for pr in rpr.get_projects():
                    if pr.id == self.id:
                        return True
                return False
        except rpr.errors.DisabledDistAPIError:
            return False

    @property
    def freezed_state(self) -> ty.Union[bool, FreezeState]:
        ret = ty.cast(
            FreezeState,
            self.get_ext_state(
                EXT_SECTION, 'project_is_freezed', pickled=True
            )
        )
        if ret:
            return ret
        return False

    @freezed_state.setter
    def freezed_state(self, state: FreezeState) -> None:
        pickled: te.Literal[True] = True
        self.set_ext_state(EXT_SECTION, 'project_is_freezed', state, pickled)
