from abc import ABCMeta, abstractmethod
from enum import IntEnum
import typing as ty
import IPy
import reapy as rpr


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


class Status(IntEnum):
    active = 1
    down = -1


class Master(metaclass=ABCMeta):
    _status: Status

    def __init__(self) -> None:
        self._status = Status.down

    @property
    @abstractmethod
    def clients(self) -> ty.List['Client']:
        raise NotImplementedError

    @property
    @abstractmethod
    def backend(self) -> 'Backend':
        raise NotImplementedError

    @property
    def status(self) -> Status:
        return self._status

    @abstractmethod
    def sync_all(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def activate(self) -> None:
        raise NotImplementedError


class Backend(metaclass=ABCMeta):
    pass


class ClientStatus(IntEnum):
    active = 1
    down = -1
    corrupted = -503


class Client(metaclass=ABCMeta):
    _name: str
    _ip: IPy.IP

    def __init__(self, name: str, ip: IPy.IP) -> None:
        self._name = name
        self._ip = ip

    @property
    @abstractmethod
    def connections(self) -> ty.List['Connection']:
        raise NotImplementedError

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, name: str) -> None:
        self._name = name

    @property
    def ip(self) -> IPy.IP:
        return self._ip

    @ip.setter
    def ip(self, ip: IPy.IP) -> None:
        self._ip = ip

    @abstractmethod
    def reconnect_all(self) -> None:
        raise NotImplementedError


class ConnectionStatus(IntEnum):
    active = 1
    unavailble_source = -2
    unavailble_dest = -3
    unavailble_all = -4


class ConnectionType(IntEnum):
    audio = 1
    midi = 2


class Connection(metaclass=ABCMeta):
    def __init__(
        self, type_: ConnectionType, source: 'ConnectionSource',
        dest: 'ConnectionDest'
    ) -> None:
        self._type = type_
        for pin in (source, dest):
            if pin.type_ is not self._type:
                raise TypeError(f'type of {pin} is {pin.type_}, used {type_}')
        self._source = source
        self._dest = dest

    @property
    @abstractmethod
    def status(self) -> ConnectionStatus:
        raise NotImplementedError

    @abstractmethod
    def reconnect(self) -> None:
        raise NotImplementedError

    @property
    def source(self) -> 'ConnectionSource':
        return self._source

    @source.setter
    def source(self, source: 'ConnectionSource') -> None:
        self._source = source

    @property
    def dest(self) -> 'ConnectionDest':
        return self._dest

    @dest.setter
    def dest(self, dest: 'ConnectionDest') -> None:
        self._dest = dest

    @property
    def type_(self) -> ConnectionType:
        return self._type


class PinStatus(IntEnum):
    active = 1
    unaccessible = -404
    disconnected = -1
    multiple_connections = 2


class ConnectionPin(metaclass=ABCMeta):
    def __init__(
        self, type_: ConnectionType, ip: IPy.IP, project: rpr.Project,
        track: rpr.Track
    ) -> None:
        self._type = type_
        self._ip = ip
        self.project = project
        self._track = track

    @property
    def ip(self) -> IPy.IP:
        return self._ip

    @ip.setter
    def ip(self, ip: IPy.IP) -> None:
        self._ip = ip

    @property
    def project(self) -> rpr.Project:
        return self._project

    @project.setter
    def project(self, project: rpr.Project) -> None:
        self._project = project

    @property
    def track(self) -> rpr.Track:
        return self._track

    @track.setter
    def track(self, track: rpr.Track) -> None:
        self._track = track

    @property
    def type_(self) -> ConnectionType:
        return self._type

    @property
    @abstractmethod
    def status(self) -> PinStatus:
        raise NotImplementedError


class ConnectionSource(ConnectionPin):
    @abstractmethod
    def connect(self, dest: 'ConnectionDest') -> None:
        raise NotImplementedError

    @property
    @abstractmethod
    def dest(self) -> ty.Optional['ConnectionDest']:
        raise NotImplementedError

    @abstractmethod
    def disconnect(self) -> None:
        raise NotImplementedError


class ConnectionDest(ConnectionPin):
    @abstractmethod
    def connect(self, source: 'ConnectionSource') -> None:
        raise NotImplementedError

    @property
    @abstractmethod
    def source(self) -> ty.Optional['ConnectionSource']:
        raise NotImplementedError

    @abstractmethod
    def disconnect(self) -> None:
        raise NotImplementedError
