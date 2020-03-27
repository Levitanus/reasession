"""Extended Track classes for dealing with several projects.

Attributes
----------
Childs : Dict[ChildAddress, Child]
    The basic index for quick iteration or retrieving tracks, that are tracked.

"""
from __future__ import annotations
import typing as ty
from enum import IntEnum
from builtins import BaseException
from types import TracebackType
import typing_extensions as te
import reapy as rpr
from reapy import reascript_api as RPR

from . import SessionError, HostIP
from .projects import Project, SlaveProject

T1 = ty.TypeVar('T1')

Childs = ty.Dict['ChildAddress', 'Child']


class ChildAddress(ty.Tuple[int, int]):
    """Represents MIDI (Bus, Channel) of child Track.

    Can be compared to tuple. All (busses/channels) are equal to one.
    """

    def __new__(cls, bus: int, channel: int) -> 'ChildAddress':
        return super().__new__(cls, (bus, channel))  # type:ignore

    def __init__(self, bus: int, channel: int) -> None:
        """Make immutable address.

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
        other = ty.cast(ty.Tuple[int, int], other)
        if other[0] != self[0]:
            for item in (other[0], self[0]):
                if item != 0:
                    return False
                else:
                    break
        if other[1] != self[1]:
            for item in (other[1], self[1]):
                if item != 0:
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
        """Make child tree leaf or branch.

        Parameters
        ----------
        track : Track
        childs : ty.Optional[Childs], optional
        """
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
        for child in childs.values():
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
        for child in childs.values():
            track = child.track
            track.target = last_target
            matched[track.id] = track
            if child.childs:
                matched.update(cls._match_secondary(child.childs, last_target))
        return matched


class TrackChildsSet(IntEnum):
    """Enum for Track.match_childs method.

    Attributes
    ----------
    both : int
        return Tuple[primary, secondary]
    primary : int
    secondary : int
    """

    both = 0
    primary = 1
    secondary = 2


class Track(rpr.Track):
    """Extended Track model, build on the top of reapy.Track.

    Attributes
    ----------
    ID : str alias for the better type hints
    id : Track.ID
        usually, `(MediaTrack*)0xNNNNNNNNNNNNNNNN`
    target : Optional[Track]
        Track in the Slave project
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
        """Extend Track model based on reapy.Track.

        Parameters
        ----------
        id : str
            name or id of Reaper track
        project : Project
            host must be specified
        childs_are_receives : bool, optional, default=True
            if False, childs will be get from sends.
        """
        super().__init__(id=id, project=project)
        self._sess_project = project
        self.target = None
        self._childs_are_receives = childs_are_receives
        self._childs = {}
        self._childs_matched_primary = {}
        self._childs_matched_secondary = {}

    @property
    def s_project(self) -> Project:
        """Stable property of Track's project, keepeng project attributes.

        Returns
        -------
        Project
        """
        return self._sess_project

    @property
    def make_current_project(self) -> ty.Callable[[], ty.ContextManager[None]]:
        """Context manager for making cjanges under the project.

        Returns
        -------
        ty.Callable[[], ty.ContextManager[None]]
        """
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
            return par == 0
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
            return par == 1
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
                childs_are_receives=self._childs_are_receives
            )
            childs = ch_tr.get_childs_tree()
            out[addr] = Child(ch_tr, childs)
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

    def connect(self) -> TrackConnect:
        """Context manager as syntax sugar.

        Note
        ----
        built on top of `reapy.connect` and `project.make_current_project`

        Returns
        -------
        ContextManager[Track]
        """
        return TrackConnect(self)

    def set_info_value(self, key: str, value: float) -> None:
        RPR.SetMediaTrackInfo_Value(self.id, key, value)  # type:ignore

    @property
    def recarm(self) -> bool:
        return bool(self.get_info_value('I_RECARM'))

    @recarm.setter
    def recarm(self, state: bool) -> None:
        self.set_info_value('I_RECARM', int(state))


class TrackConnect(ty.ContextManager[Track]):
    """Context manager as syntax sugar for several reapy's.

    Attributes
    ----------
    connect : reapy.connect
    curr_proj : reapy.Project.make_current_project()
    ir : reapy.inside_reaper
    track : Track
    """

    track: Track
    connect: rpr.connect
    curr_proj: ty.ContextManager[None]
    ir: ty.ContextManager[None]

    def __init__(self, track: Track) -> None:
        self.track = track

    def __enter__(self) -> Track:
        pr = self.track.s_project
        self.connect = rpr.connect(pr.last_ip)
        self.connect.__enter__()
        self.ir = rpr.inside_reaper()
        self.ir.__enter__()
        self.curr_proj = pr.make_current_project()
        self.curr_proj.__enter__()
        return self.track

    def __exit__(
        self, exc_type: ty.Optional[ty.Type[BaseException]],
        value: ty.Optional[BaseException],
        traceback: ty.Optional[TracebackType]
    ) -> None:
        self.curr_proj.__exit__(exc_type, value, traceback)
        self.ir.__exit__(exc_type, value, traceback)
        self.connect.__exit__(exc_type, value, traceback)


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
        """Control output data frow and slave connection.

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

    def sync_recarm(self) -> None:
        """Synchronize recarm state of all childs with target childs.

        Raises
        ------
        SessionError
            If no childs matched to slave.
        """
        if self.target is None:
            raise SessionError(f'no target for track {self.name} ({self})')
        if not self._childs_matched_primary:
            raise SessionError(f'no matched childs for {self.name} ({self})')
        childs = self._return_matched_childs(TrackChildsSet.both)
        t_host = self.s_project.last_ip
        Targets = te.TypedDict('Targets', {'target': Track, 'recarm': bool})

        with rpr.inside_reaper():
            targets: ty.Dict[Track.ID, Targets] = {}
            for child in childs.values():
                recarm = child.recarm
                assert child.target, f'no target for child: {child}'
                target = child.target
                if target.id not in targets:
                    targets[target.id] = {'target': target, 'recarm': recarm}
                elif recarm is True:
                    targets[target.id]['recarm'] = True
        with rpr.connect(t_host):
            with rpr.inside_reaper():
                with self.target.make_current_project():
                    for t_dict in targets.values():
                        target = t_dict['target']
                        recarm = t_dict['recarm']
                        target.recarm = recarm

    def update(self) -> None:
        """Update state of the Track.

        Note
        ----
        May take a long
        """
        self._childs = {}
        self._childs_matched_primary = {}
        self.match_childs()
        self.sync_recarm()


class SlaveInTrack(Track):
    """Controls input stream of slave project."""

    project: SlaveProject

    def __init__(
        self,
        id: str,
        project: SlaveProject,
        childs_are_receives: bool = False
    ) -> None:
        """Control input stream of slave project.

        Parameters
        ----------
        track : rpr.Track
        childs_are_receives : bool, optional
            False by default, as input childs are sends.
        """
        assert isinstance(project, SlaveProject)
        super().__init__(id, project, childs_are_receives)

    @property
    def host(self) -> HostIP:
        """Slave host IP address (last seen).

        Returns
        -------
        HostIP
        """
        return self.s_project.last_ip
