"""Abstract interfaces for connections backends.

The main ABC Connector has to be realized by the concrete backend.
At the moment only midi-forwarding from master to slave is
attempted to be implemented here.
"""

from abc import ABC, abstractmethod
import typing as ty
import typing_extensions as te
import reapy as rpr


class ConnectionsError(Exception):
    """Base class for any package-specific errors."""


class SlaveTrack(te.TypedDict):
    """Dictionary represents slave-side track of OutTrack.

    Parameters
    ----------
    host: str
    track: reapy.Track

    """

    host: str
    track: rpr.Track


class OutTrack(te.TypedDict):
    """Dictionary represents track, sending midi to slave.

    Parameters
    ----------
    track: reapy.Track
    slave: SlaveTrack

    """

    track: rpr.Track
    slave: SlaveTrack


class HostInfo(te.TypedDict):
    """Communication protocol between daemon and connection backend.

    Parameters
    ----------
    host: str
    in_tracks: List[reapy.Track]
    out_tracks: List[OutTrack]

    """

    host: str
    in_tracks: ty.List[rpr.Track]
    out_tracks: ty.List[OutTrack]


class Connector(ABC):
    """ABC for communication between daemon and connection backend.

    method 'connect()' will be called each time connected tracks are updated,
    including: closing of slave project, disconnection from slave etc.

    Expected behaviour of 'connect_all()' is to establish connection between
    given tracks on their hosts. For example, if backend is Jack -> out tracks
    of master will be connected to the propriate midi-hardware-outputs and
    slave tracks will be connected to the appropriate hardware inputs.
    """

    def __init__(self, hosts: ty.List[HostInfo]) -> None:
        """ABC for communication and connection backend.

        Parameters
        ----------
        hosts : List[HostInfo]
            see HostInfo

        """
        self._hosts = hosts

    @property
    def hosts(self) -> ty.List[HostInfo]:
        """Read-only property.

        Returns
        -------
        List[HostInfo]

        """
        return self._hosts

    def update(self, hosts: ty.List[HostInfo]) -> None:
        """Update hosts list of Connector.

        Called by the Connector user.

        Parameters
        ----------
        hosts : List[HostInfo]

        """
        self._hosts = hosts
        self.connect_all()

    @abstractmethod
    def connect_all(self) -> None:
        """Connect master tracks to slave.

        See jack_backend.py for details.

        """
        ...
