from __future__ import annotations
from types import TracebackType
from builtins import BaseException
import typing as ty
import typing_extensions as te
import reapy as rpr
from uuid import uuid4
from contextlib import contextmanager

import reasession as rs
from reasession import session as ss

from . import SessionError, SlaveUnacessible, HostIP, FreezeState
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
    GUID_T = ty.NewType('GUID_T', str)
    _guid: ty.Optional[GUID_T]
    ID = ty.NewType('ID', str)
    id: ID

    def __init__(
        self, id: ty.Union[str, int], ip: HostIP = HostIP('localhost')
    ) -> None:
        self._host_ip = ip
        self._host = None
        self._guid = None
        super().__init__(id)

    @property
    def GUID(self) -> Project.GUID_T:
        """Syntax sugar to keep Project unique.

        :type: Project.GUID_T
        """
        if self._guid is not None:
            return self._guid
        self._guid = ty.cast(
            Project.GUID_T, self.get_ext_state(EXT_SECTION, 'guid')
        )
        if self._guid == '':
            self._guid = self.GUID_new()
        return self._guid

    def GUID_new(self) -> Project.GUID_T:
        """Put new GUID into the project.

        Returns
        -------
        Project.GUID_T
        """
        self._guid = ty.cast(Project.GUID_T, str(uuid4()))
        self.set_ext_state(EXT_SECTION, 'guid', self._guid)
        return self._guid

    @rpr.inside_reaper()
    def __getstate__(self) -> ty.Dict[str, object]:
        state = self.__dict__
        s_id = self.GUID
        state['_guid'] = s_id
        return state

    @rpr.inside_reaper()
    def __setstate__(self, state: ty.Dict[str, object]) -> None:
        guid = state['_guid']
        for pr in rpr.get_projects():
            if pr.get_ext_state(EXT_SECTION, 'guid') == guid:
                state['id'] = pr.id
                for k, v in state.items():
                    self.__dict__[k] = v
                return
        raise KeyError(f"cannot find project with guid {guid}")

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
    master_track: ss.Track
    _id: ty.Optional[Project.ID]

    # subproject: SlaveSubProject

    # master_out_tracks: ty.Dict[MasterOutrs.Track.ID, MasterOutrs.Track]
    # slave_in_tracks: ty.Dict[SlaveInrs.Track.ID, SlaveInrs.Track]
    # freezed: bool
    # disabled: bool
    # unloaded: bool

    def __init__(
        self, id: ty.Union[str, int], ip: HostIP = HostIP('localhost')
    ) -> None:
        super().__init__(id, ip)
        self._id = self.id

    @property  # type:ignore
    def id(self) -> Project.ID:  # type:ignore
        if self._id is None:
            if self._guid is None:
                raise SessionError(
                    'Something is very wrong during slave instantiation'
                )
            raise SlaveUnacessible(
                f'Slave with guid {self.GUID} can not be found'
            )
        return self._id

    @id.setter
    def id(self, id_: ty.Optional[ty.Union[str, int]]) -> None:
        if isinstance(id_, str) and id_.startswith('(ReaProject*)0x'):
            self._id = ty.cast(Project.ID, id_)
            return
        self._id = ty.cast(Project.ID, rpr.Project(id_).id)

    def __setstate__(self, state: ty.Dict[str, object]) -> None:
        try:
            super().__setstate__(state)
        except KeyError:
            self.__dict__ = state
        self._id = None

    @property
    def is_accessible(self) -> bool:
        try:
            with self.host:
                for pr in rpr.get_projects():
                    if pr.id == self.id:
                        return True
                return False
        except (rpr.errors.DisabledDistAPIError, SlaveUnacessible):
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
