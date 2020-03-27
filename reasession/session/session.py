import reapy as rpr
import typing as ty
import asyncio as io
# from collections import
from reasession.session.projects import Project, Host, SlaveProject
from reasession.session.misc import HostIP
import reasession.session.tracks as trs
from reasession.config import EXT_SECTION
import reasession.connections.jack_backend as jbck
import reasession.connections.interface as cif


class ExtState:

    def __init__(self, project: Project) -> None:
        self._pr = project
        self._keys = ['slave']

    def __getitem__(self, key: str) -> object:
        return self._pr.get_ext_state(EXT_SECTION, key, pickled=True)

    def __setitem__(self, key: str, value: object) -> None:
        self._pr.set_ext_state(EXT_SECTION, key, value, pickled=True)


SlavesDict = ty.Dict[trs.Track.ID, SlaveProject]


class SessionLoader:

    def __init__(self, master: Project) -> None:
        self._master = master
        self._ext_state = ExtState(master)

    @property
    def ext_state(self) -> ExtState:
        return self._ext_state

    @property
    def slaves(self) -> SlavesDict:
        return ty.cast(SlavesDict, self.ext_state['slaves'])

    @slaves.setter
    def slaves(self, slaves: SlavesDict) -> None:
        self.ext_state['slaves'] = slaves

    def add_slave(self, slave: SlavesDict) -> None:
        slaves = self.slaves
        slaves.update(slave)
        self.slaves = slaves

    def remove_slave(
        self,
        slave: ty.Optional[SlavesDict] = None,
        out_track: ty.Optional[trs.Track.ID] = None
    ) -> None:
        if (slave, out_track) is (None, None):
            raise TypeError('at least 1 parameter has to be passed')
        if slave and not out_track:
            out_track = list(slave.keys())[0]
        slaves = self.slaves
        del slaves[ty.cast(trs.Track.ID, out_track)]


class Session:

    def __init__(
        self,
        master: Project,
        connector_class: ty.Type[cif.Connector] = jbck.Connector
    ) -> None:
        self._master = master
        self._hosts: ty.Set[Host] = set([Host(ip=HostIP('localhost'))])
        self._connector_cl = connector_class

    def host_add(self, host: Host) -> None:
        with rpr.connect(host.ip):
            self._hosts.add(host)

    def hosts_check(self) -> None:
        availble = set()
        for host in self._hosts:
            try:
                with rpr.connect(host.ip):
                    continue
            except rpr.errors.DisabledDistAPIError:
                availble.add(host)
        self._hosts &= availble
