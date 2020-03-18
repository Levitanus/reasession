from __future__ import annotations
import typing as ty
import typing_extensions as te
import reapy as rpr
from reapy import reascript_api as RPR
from pathlib import Path
from uuid import uuid4, UUID
from .connections import interface as conn

Childs = ty.Dict['ChildAddress', 'Child']


class ChildAddress(ty.Tuple[int, int]):

    def __new__(cls, bus: int, channel: int) -> 'ChildAddress':
        ...

    def __init__(self, bus: int, channel: int) -> None:
        ...

    @property
    def bus(self) -> int:
        ...

    @property
    def channel(self) -> int:
        ...

    def __eq__(self, other: object) -> bool:
        ...

    def __repr__(self) -> str:
        ...

    def __hash__(self) -> int:
        ...


class Child:
    track: 'Track'
    childs: Childs

    def __init__(
        self, track: 'Track', childs: ty.Optional[Childs] = None
    ) -> None:
        ...

    def __repr__(self) -> str:
        reveal_type(self.childs)
        retstr = 'Child(Track={}, childs={})'.format(
            self.track.name, self.childs)
        return retstr


class Track:
    """Extended Track model, build on the top of reapy.Track.

    Attributes
    ----------
    ID : str alias for the better type hints
    id_ : Track.ID
        usually, `(MediaTrack*)0xNNNNNNNNNNNNNNNN`
    target : Optional[Track]
        Track in the Slave project
    track : reapy.Track
    """

    ID = ty.NewType('ID', UUID)
    id_: ID
    _BUS_FX_NAME: te.Literal[
        '(Levitanus): pack MIDI BUSes to one channel or unpack them'
    ] = '(Levitanus): pack MIDI BUSes to one channel or unpack them'
    _BUS_PAR_IDX: te.Literal[0] = 0
    target: ty.Optional[Track]
    _track: rpr.Track
    _childs: ty.Dict[Track.ID, Track]
    _childs_matched: ty.Dict[Track.ID, Track]

    @property
    def name(self) -> str:
        ...
