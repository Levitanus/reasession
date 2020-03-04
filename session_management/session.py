from __future__ import annotations
import typing as ty
import typing_extensions as te
import reapy as rpr
from reapy import reascript_api as RPR
from pathlib import Path
from uuid import uuid4, UUID
from .connections import interface as conn

MidiBus = ty.NewType('MidiBus', int)
HostIP = ty.NewType('HostIP', str)


class MasterOutTrack:
    ID = ty.NewType('ID', UUID)
    _id: ID
    track: rpr.Track
    childs: ty.Dict[MasterMidiTrack.ID, MasterMidiTrack]
    slave: SlaveProject
    target: SlaveInTrack


class _MasterMidiTrackTarget(te.TypedDict):
    host: HostIP
    project: rpr.Project
    track: SlaveInstTrack
    rpr_track: rpr.Track


class MasterMidiTrack:
    ID = ty.NewType('ID', UUID)
    _id: ID
    track: rpr.Track
    out_track: MasterOutTrack
    out_bus: MidiBus
    selected: bool
    dirty: bool

    @property
    def target(self) -> _MasterMidiTrackTarget:
        host = self.out_track.slave.last_ip
        project = self.out_track.slave.project.project
        track = self.out_track.target.childs[self.out_bus]
        rpr_track = track.track
        return _MasterMidiTrackTarget(
            host=host, project=project, track=track, rpr_track=rpr_track
        )


class SubProxy:
    file: Path


class SlaveSubProject:
    proxy: SubProxy
    temp_file: Path


class SlaveProject:
    ID = ty.NewType('ID', UUID)
    _id: ID
    project: Project
    dirty: bool
    master_track: rpr.Track
    subproject: SlaveSubProject
    acessible: bool
    last_ip: HostIP
    master_out_tracks: ty.Dict[MasterOutTrack.ID, MasterOutTrack]
    slave_in_tracks: ty.Dict[SlaveInTrack.ID, SlaveInTrack]
    freezed: bool
    disabled: bool
    unloaded: bool


class SlaveInTrack:
    ID = ty.NewType('ID', UUID)
    _id: ID
    track: rpr.Track
    childs: ty.Dict[MidiBus, SlaveInstTrack]
    project: SlaveProject


class SlaveInstTrack:
    ID = ty.NewType('ID', UUID)
    _id: ID
    track: rpr.Track
    in_track: SlaveInTrack
    in_bus: MidiBus
    armed: bool
    freezed: bool
    disabled: bool
    unloaded: bool


class ShareProjectData:
    tempo_track: object


class Project:
    project: rpr.Project

    def get_share_data(self) -> ShareProjectData:
        raise NotImplementedError

    def set_share_data(self, data: ShareProjectData) -> None:
        raise NotImplementedError


class SlaveTemplate:
    template_path: Path

    def create_master_tracks(self) -> None:
        raise NotImplementedError

    def create_slave_project(self, ip: HostIP) -> SlaveProject:
        raise NotImplementedError


class SessionTree:
    master: Project
    connector: conn.Connector
    slaves: ty.Dict[SlaveProject.ID, SlaveProject]
    out_tracks: ty.Dict[MasterOutTrack.ID, MasterOutTrack]
    midi_tracks: ty.Dict[MasterMidiTrack.ID, MasterMidiTrack]
    session_file: SessionFile
    availble_hosts: ty.List[HostIP]

    def new_slave(
        self, ip: HostIP, project: ty.Optional[SlaveTemplate]
    ) -> SlaveProject:
        raise NotImplementedError

    def save_session(self, file: ty.Optional[Path]) -> SessionFile:
        raise NotImplementedError

    def is_dirty(self) -> bool:
        raise NotImplementedError

    def reconnect(self) -> None:
        host_info = self._build_host_info()
        self.connector.update(host_info)
        self.connector.connect_all()

    def _build_host_info(self) -> ty.List[conn.HostInfo]:
        raise NotImplementedError

    def rebuild(self) -> None:
        raise NotImplementedError


class SessionFile:

    def get_slave_file(self, slave: SlaveProject) -> Path:
        raise NotImplementedError
