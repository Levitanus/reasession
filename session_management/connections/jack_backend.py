import IPy
import typing as ty
from os import system
from time import sleep

import jack
import reapy as rpr

from . import interface as aif


class JackBackend(aif.Backend):
    def __init__(self, name: str, init_string: str, is_master: bool) -> None:
        no_start = True
        if is_master:
            no_start = False
        init_args = dict(
            name=name,
            use_exact_name=True,
            no_start_server=no_start,
            servername=None,
            session_id=None
        )
        system(init_string)
        try:
            self.client = jack.Client(**init_args)
        except jack.JackOpenError:
            sleep(.5)
            self.client = jack.Client(**init_args)
        self.name = name

    def force_connect(self, source: jack.Port, destination: jack.Port) -> None:
        try:
            self.client.connect(source, destination)
        except jack.JackErrorCode as e:
            if not e.code == 17:
                raise e


class Master(aif.Master):
    _status: aif.Status

    def __init__(self) -> None:
        super().__init__()

    @property
    def clients(self) -> ty.List[aif.Client]:
        raise NotImplementedError

    @property
    def backend(self) -> JackBackend:
        raise NotImplementedError

    def sync_all(self) -> None:
        raise NotImplementedError

    def activate(self) -> None:
        raise NotImplementedError


class Client(aif.Client):
    def __init__(self, name: str, ip: IPy.IP) -> None:
        super().__init__(name, ip)

    @property
    def connections(self) -> ty.List[aif.Connection]:
        raise NotImplementedError

    def reconnect_all(self) -> None:
        raise NotImplementedError


class Connection(aif.Connection):
    def __init__(
        self, type_: aif.ConnectionType, source: 'ConnectionSource',
        dest: 'ConnectionDest'
    ) -> None:
        super().__init__(type_, source, dest)

    @property
    def status(self) -> aif.ConnectionStatus:
        raise NotImplementedError

    def reconnect(self) -> None:
        raise NotImplementedError


class ConnectionPin(aif.ConnectionPin):
    def __init__(
        self, type_: aif.ConnectionType, ip: IPy.IP, project: rpr.Project,
        track: rpr.Track, backend: JackBackend
    ) -> None:
        super().__init__(type_=type_, ip=ip, project=project, track=track)
        self.backend = backend

    @property
    def status(self) -> aif.PinStatus:
        if not self.is_accessible():
            return aif.PinStatus.unaccessible

        # with rpr.connect(self.ip.strNormal()):
        #     pass


class ConnectionSource(aif.ConnectionSource, ConnectionPin):
    def connect(self, dest: aif.ConnectionDest) -> None:
        raise NotImplementedError

    @property
    def dest(self) -> ty.Optional[aif.ConnectionDest]:
        raise NotImplementedError

    def disconnect(self) -> None:
        raise NotImplementedError


class ConnectionDest(aif.ConnectionDest, ConnectionPin):
    def connect(self, source: aif.ConnectionSource) -> None:
        raise NotImplementedError

    @property
    def source(self) -> ty.Optional[aif.ConnectionSource]:
        raise NotImplementedError

    def disconnect(self) -> None:
        raise NotImplementedError
