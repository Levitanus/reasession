from __future__ import annotations
import typing as ty
import typing_extensions as te
import reapy as rpr
from reapy import reascript_api as RPR
from pathlib import Path
from uuid import uuid4, UUID
from .connections import interface as conn
from enum import IntEnum
from contextlib import contextmanager
from builtins import BaseException
from types import TracebackType

MidiBus = ty.NewType('MidiBus', int)
HostIP = ty.NewType('HostIP', str)
T1 = ty.TypeVar('T1')

Childs = ty.Dict['ChildAddress', 'Child']


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


class ChildAddress(ty.Tuple[int, int]):
    """Represents MIDI (Bus, Channel) of child Track.

    Can be compared to tuple. All (busses/channels) are equal to one.
    """

    def __new__(cls, bus: int, channel: int) -> 'ChildAddress':
        return super().__new__(cls, (bus, channel))  # type:ignore

    def __init__(self, bus: int, channel: int) -> None:
        """make immutable address.

        Parameters
        ----------
        bus : int
        channel : int
        """
        super().__init__()

    @property
    def bus(self) -> int:
        """MIDI Bus.

        Returns
        -------
        int
            0 if All buses
            -1 if no midi routing
        """
        return self[0]

    @property
    def channel(self) -> int:
        """Midi Channel.

        Returns
        -------
        int
            0 if All channels
            -1 if no midi routing
        """
        return self[1]

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ty.Sequence):
            return False
        if len(other) != 2:
            return False
        for item in other:
            if not isinstance(item, int):
                return False
            if item > 16:
                return False
        if other[0] != self[0]:  # type:ignore
            for item in (other[0], self[0]):
                if item != 0:  # type:ignore
                    return False
                else:
                    break
        if other[1] != self[1]:  # type:ignore
            for item in (other[1], self[1]):
                if item != 0:  # type:ignore
                    return False
                else:
                    break
        return True

    def __repr__(self) -> str:
        return f'ChildAddress(bus={self.bus}, channel={self.channel})'

    def __hash__(self) -> int:
        return hash((self[0], self[1]))


class Child:
    """Represents tree branch of track recieves.

    Attributes
    ----------
    track : Track
        Will be modified in several cases (`target` attribute)
    childs : Childs
        the branch itself, if it's not a leaf.
    """

    track: 'Track'
    childs: Childs

    def __init__(
        self, track: 'Track', childs: ty.Optional[Childs] = None
    ) -> None:
        self.track = track
        if not childs:
            childs = {}
        self.childs = childs

    def __repr__(self) -> str:
        return f'Child(Track={self.track.name}, childs={self.childs})'

    @classmethod
    def match(
        cls, childs_out: Childs, childs_in: Childs, last_target: Track
    ) -> ty.Tuple[ty.Dict['Track.ID', 'Track'], ty.Dict['Track.ID', 'Track']]:
        """Match two childs trees for making index of track targets.

        Parameters
        ----------
        childs_out : Childs
            Childs of master track connected to slave.
        childs_in : Childs
            Childs of slave track connected to master.
        last_target : Track
            In case of making from the master out track it has to be slave in.
            Also invoked inside itself if childs have childs.

        Returns
        -------
        Tuple[matched_primary: Dict['Track.ID', 'Track'],
                matched_secondary: Dict['Track.ID', 'Track']]
            matched_primary are tracks connected directly to targets
            matched_secondary are tracks connected to the primary targets
        """
        matched_primary: ty.Dict[Track.ID, Track] = {}
        matched_secondary: ty.Dict[Track.ID, Track] = {}
        for key, child in childs_out.items():
            track = child.track
            c_p, c_s = cls._try_match_primary(key, childs_in, track, child)
            matched_primary.update(c_p)
            matched_secondary.update(c_s)
            if not c_p:
                track.target = last_target
                matched_secondary[track.id] = track
                if child.childs:
                    matched_secondary.update(
                        cls._match_secondary(child.childs, last_target)
                    )
        return matched_primary, matched_secondary

    @classmethod
    def unpack(cls, childs: Childs) -> ty.Dict['Track.ID', 'Track']:
        """Get index dict from the childs tree.

        Parameters
        ----------
        childs : Childs

        Note
        ----
        Tracks will not be matched to target.

        Returns
        -------
        Dict['Track.ID', 'Track']
        """
        unpacked: ty.Dict[Track.ID, Track] = {}
        for key, child in childs.items():
            track = child.track
            unpacked[track.id] = track
            if child.childs:
                unpacked.update(child.unpack(child.childs))
        return unpacked

    @staticmethod
    def _try_match_primary(
        key: ChildAddress, childs_in: Childs, track: Track, child: Child
    ) -> ty.Tuple[ty.Dict['Track.ID', 'Track'], ty.Dict['Track.ID', 'Track']]:
        c_p: ty.Dict['Track.ID', 'Track'] = {}
        c_s: ty.Dict['Track.ID', 'Track'] = {}
        if key in childs_in:
            temp_last_target = childs_in[key].track
            track.target = temp_last_target
            if child.childs:
                c_p, c_s = Child.match(
                    child.childs, childs_in[key].childs, temp_last_target
                )
            c_p.update({track.id: track})
        return c_p, c_s

    @classmethod
    def _match_secondary(cls, childs: Childs,
                         last_target: Track) -> ty.Dict['Track.ID', 'Track']:
        matched: ty.Dict[Track.ID, Track] = {}
        for key, child in childs.items():
            track = child.track
            track.target = last_target
            matched[track.id] = track
            if child.childs:
                matched.update(cls._match_secondary(child.childs, last_target))
        return matched


class TrackChildsSet(IntEnum):
    both = 0
    primary = 1
    secondary = 2


class Track(rpr.Track):
    """Extended Track model, build on the top of reapy.Track.

    Attributes
    ----------
    ID : str alias for the better type hints
    id_ : Track.ID
        usually, `(MediaTrack*)0xNNNNNNNNNNNNNNNN`
    target : Optional[Track]
        Track in the Slave project
    track : reapy.Track
    name : str
    """

    ID = ty.NewType('ID', str)
    id: ID
    target: ty.Optional[Track]
    project: Project
    _BUS_FX_NAME: te.Literal[
        '(Levitanus): pack MIDI BUSes to one channel or unpack them'
    ] = '(Levitanus): pack MIDI BUSes to one channel or unpack them'
    _BUS_PAR_IDX: te.Literal[0] = 0
    _childs: ty.Dict[Track.ID, Track]
    _childs_matched_primary: ty.Dict[Track.ID, Track]
    _childs_matched_secondary: ty.Dict[Track.ID, Track]
    _childs_are_receives: bool

    def __init__(
        self, id: str, project: Project, childs_are_receives: bool = True
    ) -> None:
        """Extended Track model, build on the top of reapy.Track.

        Parameters
        ----------
        track : rpr.Track
        """
        super().__init__(id=id, project=project)
        self._sess_project = project
        self.target = None
        self._childs_are_receives = childs_are_receives
        self._childs = {}
        self._childs_matched_primary = {}
        self._childs_matched_secondary = {}

    # def __repr__(self) -> str:
    #     return f'{self.__module__}.Track(name={self.name})'

    @property
    def s_project(self) -> Project:
        return self._sess_project

    @property
    def make_current_project(self) -> ty.Callable[[], ty.ContextManager[None]]:
        return self.project.make_current_project

    @property
    def buses_packed(self) -> bool:
        """Whether MIDI BUSes are packed to one channel or not.

        Note
        ----
        currently it's made by the custom JSFX

        Returns
        -------
        bool
        """
        with rpr.inside_reaper():
            fxlist = self.fxs
            try:
                fx = fxlist[self._BUS_FX_NAME]
                par = fx.params[self._BUS_PAR_IDX]
            except KeyError:
                return False
            return par.normalized == 0
        return False

    @property
    def buses_unpacked(self) -> bool:
        """Whether MIDI BUSes are unpacked from one channel or not.

        Note
        ----
        currently it's made by the custom JSFX

        Returns
        -------
        bool
        """
        with rpr.inside_reaper():
            fxlist = self.fxs
            try:
                fx = fxlist[self._BUS_FX_NAME]
                par = fx.params[self._BUS_PAR_IDX]
            except KeyError:
                return False
            return par.normalized == 1
        return False

    def get_childs_tree(self) -> Childs:
        """Get tree-like collection of tracks, connected by receives.

        Returns
        -------
        Childs
        """
        out: Childs = {}
        if self._childs_are_receives:
            ch_t = self.receives
        else:
            ch_t = self.sends
        for rcv in ch_t:
            if self._childs_are_receives:
                source = rcv.source_track
                midi_d = rcv.midi_dest
            else:
                source = rcv.dest_track
                midi_d = rcv.midi_source
            if midi_d == (-1, -1):
                continue
            addr = ChildAddress(*midi_d)
            ch_tr = Track(
                id=source.id,
                project=Project(source.project.id, self.s_project.last_ip),
                childs_are_receives=self._childs_are_receives  # type:ignore
            )
            childs = ch_tr.get_childs_tree()  # type:ignore
            out[addr] = Child(ch_tr, childs)  # type:ignore
        return out

    @property
    def childs(self) -> ty.Dict[Track.ID, Track]:
        """Flat dict of all childs.

        Returns
        -------
        ty.Dict[Track.ID, Track]
        """
        ch_d = self._childs
        if ch_d:
            return ch_d
        with self.make_current_project():
            ch_tree = self.get_childs_tree()
        return Child.unpack(ch_tree)

    def match_childs(self, childs_set: TrackChildsSet = TrackChildsSet.both
                     ) -> ty.Dict[Track.ID, Track]:
        """Flat collection of childs, matched to the slave tracks.

        Returns
        -------
        ty.Dict[Track.ID, Track]

        Raises
        ------
        SessionError
            If no target set for the Track.
        """
        # self._childs_matched
        if self._childs_matched_primary:
            return self._return_matched_childs(childs_set)
        if not self.target:
            raise SessionError(f'track {self} has no target')
        s_ch_tree = self.get_childs_tree()
        with self.target.make_current_project():
            t_ch_tree = self.target.get_childs_tree()
        self._childs_matched_primary, self._childs_matched_secondary = \
            Child.match(
                s_ch_tree, t_ch_tree, self.target
            )
        return self._return_matched_childs(childs_set)

    def _return_matched_childs(
        self, childs_set: TrackChildsSet = TrackChildsSet.both
    ) -> ty.Dict[Track.ID, Track]:
        if childs_set == TrackChildsSet.both:
            return {
                **self._childs_matched_primary,
                **self._childs_matched_secondary
            }
        if childs_set == TrackChildsSet.primary:
            return self._childs_matched_primary
        if childs_set == TrackChildsSet.secondary:
            return self._childs_matched_secondary
        raise SessionError(f"can't recognize argument: {childs_set}")

    def connect(self) -> ty.ContextManager[Track]:
        """Context manager as syntax sugar.

        Note
        ----
        built on top of `reapy.connect` and `project.make_current_project`

        Returns
        -------
        SlaveInTrack
        """
        return TrackConnect(self)


class TrackConnect(ty.ContextManager[Track]):
    track: Track
    connect: rpr.connect
    curr_proj: ty.ContextManager[None]
    ir: ty.ContextManager[None]

    def __init__(self, track: Track) -> None:
        self.track = track

    def __enter__(self) -> Track:
        pr = self.track.project
        self.connect = rpr.connect(pr.last_ip)
        self.connect.__enter__()  # type:ignore
        self.ir = rpr.inside_reaper()  # type:ignore
        self.ir.__enter__()  # type:ignore
        self.curr_proj = pr.make_current_project()  # type:ignore
        self.curr_proj.__enter__()  # type:ignore
        return self.track  # type:ignore

    def __exit__(
        self, type: ty.Optional[ty.Type[BaseException]],
        value: ty.Optional[BaseException],
        traceback: ty.Optional[TracebackType]
    ) -> None:
        self.curr_proj.__exit__(type, value, traceback)
        self.ir.__exit__(type, value, traceback)
        self.connect.__exit__(type, value, traceback)


class MasterOutTrack(Track):
    """Controls output data flow and slave connection.

    Attributes
    ----------
    slave : SlaveProject
        to connect with
    target : SlaveInTrack
        to track of
    """

    slave: SlaveProject
    target: SlaveInTrack

    def __init__(
        self, id: str, project: Project, target: SlaveInTrack
    ) -> None:
        """Controls output data frol and slave connection.

        Parameters
        ----------
        id : str
            the same as reapy.Project parameter
        project : Project
            parent project
        target : SlaveInTrack
            track, which is slave alter-ego
        """
        super().__init__(id, project)
        self.slave = target.project
        self.target = target


class SlaveInTrack(Track):
    """Controls input stream of slave project."""
    project: SlaveProject

    def __init__(
        self,
        id: str,
        project: SlaveProject,
        childs_are_receives: bool = False
    ) -> None:
        """Controls input stream of slave project.

        Parameters
        ----------
        track : rpr.Track
        childs_are_receives : bool, optional
            False by default, as input childs are sends.
        """
        assert isinstance(project, SlaveProject)
        super().__init__(id, project, childs_are_receives)

    # @property
    # def project(self) -> SlaveProject:
    #     Slave project, keeps the Track.

    #     Returns
    #     -------
    #     SlaveProject

    #     return self._project

    @property
    def host(self) -> HostIP:
        """Slave host IP address (last seen).

        Returns
        -------
        HostIP
        """
        return self.project.last_ip


class Project(rpr.Project):
    _host_ip: HostIP

    def __init__(
        self, id: ty.Union[str, int], ip: HostIP = HostIP('localhost')
    ) -> None:
        self._host_ip = ip
        super().__init__(id)

    # @property
    # def _args(self) -> ty.Tuple[str, HostIP]:  # type:ignore
    #     original = super()._args
    #     return (*original, self.last_ip)  # type:ignore

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
    # def _args(self) -> ty.Tuple[str, HostIP]:  # type:ignore
    #     original = super()._args
    #     return (*original, self.last_ip)
