import typing as ty
import typing_extensions as te
import re
from abc import ABC, abstractmethod
import reapy as rpr
from reapy import reascript_api as RPR
import jack
import warnings
from session_management import persistence
from . import interface as iface

from IPy import IP

CONN_NAME_REGEXP = re.compile(r'(.+):(.+)')


class PortNameError(Exception):
    pass


class _PortDump(te.TypedDict):
    host: str
    name: str
    uuid: str


class _ReaperPort(te.TypedDict):
    idx: int
    name: str


class _JConnection(te.TypedDict):
    host: str
    name: str


class _JMidiPort(te.TypedDict):
    name: str
    connection: _JConnection


class _RMidiPort(te.TypedDict):
    idx: int
    name: str


_RSlaveTrack = iface.SlaveTrack
_ROutTrack = iface.OutTrack


class _HostInfo(te.TypedDict):
    host: str
    reaper_in_ports: ty.List[_RMidiPort]
    jack_in_ports: ty.List[_JMidiPort]
    in_tracks: ty.List[rpr.Track]
    reaper_out_ports: ty.List[_RMidiPort]
    jack_out_ports: ty.List[_JMidiPort]
    out_tracks: ty.List[_ROutTrack]


class _RTrackPort(te.TypedDict):
    host: str
    track: rpr.Track
    port: _RMidiPort


class _RHostPort(te.TypedDict):
    host: str
    port: _RMidiPort
    dest_host: str


def parce_port_name(port: jack.Port) -> ty.Tuple[str, str]:
    m = re.match(CONN_NAME_REGEXP, port.name)
    if not m:
        raise PortNameError(f'strange port name: {port.name}')
    return ty.cast(ty.Tuple[str, str], m.groups())


def get_jack_ports_parametrized(want_output: bool = False
                                ) -> ty.List[_JMidiPort]:
    is_input = not want_output
    is_output = want_output
    # print(is_input, is_output)
    client = jack.Client('observer')
    ports = client.get_ports(
        r'REAPER.+', is_midi=True, is_output=is_output, is_input=is_input
    )
    # print([p.name for p in ports])
    midi_ports: ty.List[_JMidiPort] = []
    for port in ports:
        connections = client.get_all_connections(port)
        # print(connections)
        if len(connections) == 1:
            _, port_name = parce_port_name(port)
            c_host, c_name = parce_port_name(connections[0])
            midi_ports.append(
                _JMidiPort(
                    name=port_name,
                    connection=_JConnection(host=c_host, name=c_name)
                )
            )
    return midi_ports


def get_jack_ports() -> ty.Tuple[ty.List[_JMidiPort], ty.List[_JMidiPort]]:
    j_ins = get_jack_ports_parametrized()
    j_outs = get_jack_ports_parametrized(True)
    return j_ins, j_outs


def set_track_midi_out(
    track: rpr.Track, out_idx: int, out_ch: int = 0
) -> None:
    CH_BITS = 5
    value = (out_idx << CH_BITS) + out_ch
    RPR.SetMediaTrackInfo_Value(track.id, 'I_MIDIHWOUT', value)  # type:ignore


def set_track_midi_in(track: rpr.Track, out_idx: int, out_ch: int = 0) -> None:
    MIDI_FLAG = 4096
    CH_BITS = 5
    value = MIDI_FLAG + (out_idx << CH_BITS) + out_ch
    RPR.SetMediaTrackInfo_Value(track.id, 'I_RECINPUT', value)  # type:ignore


def match_host_ports_parametrized(
    r_ports: ty.List[_RMidiPort],
    j_ports: ty.List[_JMidiPort],
    hostname: str,
) -> ty.List[_RHostPort]:
    out: ty.List[_RHostPort] = []

    def validate_name(r_port: _RMidiPort, j_port: _JMidiPort) -> bool:
        if r_port['name'] == j_port['name']:
            return True
        if r_port['name'].startswith(j_port['connection']['host']):
            if r_port['name'].endswith(j_port['connection']['name']):
                return True
        return False

    for r_port in r_ports:
        for j_port in j_ports:
            if validate_name(r_port, j_port):
                dest_host = j_port['connection']['host']
                if hostname == 'localhost' and dest_host == 'system':
                    continue
                if hostname != 'localhost' and dest_host == 'system':
                    dest_host = 'localhost'
                if dest_host == 'REAPER':
                    dest_host = 'localhost'
                out.append(
                    dict(
                        host=hostname,
                        port=r_port,
                        dest_host=dest_host,
                    )
                )
    return out


def match_host_ports(host: _HostInfo
                     ) -> ty.Tuple[ty.List[_RHostPort], ty.List[_RHostPort]]:
    r_in_ports = host['reaper_in_ports']
    j_in_ports = host['jack_in_ports']
    r_out_ports = host['reaper_out_ports']
    j_out_ports = host['jack_out_ports']

    ins: ty.List[_RHostPort] = match_host_ports_parametrized(
        r_ports=r_in_ports,
        j_ports=j_in_ports,
        hostname=host['host'],
    )
    outs = match_host_ports_parametrized(
        r_ports=r_out_ports,
        j_ports=j_out_ports,
        hostname=host['host'],
    )
    return ins, outs


def get_connection_task(
    hosts: ty.Sequence[_HostInfo]
) -> ty.Tuple[ty.List[_RTrackPort], ty.List[_RTrackPort]]:
    midi_outs: ty.List[_RTrackPort] = []
    midi_ins: ty.List[_RTrackPort] = []

    for host in hosts:
        hostname = host['host']
        h_ports_in, h_ports_out = match_host_ports(host)
        for track in host['in_tracks']:
            for idx, port in enumerate(h_ports_in):
                if port['dest_host'] == 'localhost':
                    midi_ins.append(
                        {
                            'host': hostname,
                            'track': track,
                            'port': h_ports_in.pop(idx)['port']
                        }
                    )
                    break
        for o_track in host['out_tracks']:
            for idx, port in enumerate(h_ports_out):
                if port['dest_host'] == o_track['slave']['host']:
                    midi_outs.append(
                        {
                            'host': hostname,
                            'track': o_track['track'],
                            'port': h_ports_out.pop(idx)['port']
                        }
                    )
                    break

    return midi_outs, midi_ins


def connect_by_task(
    task: ty.Tuple[ty.List[_RTrackPort], ty.List[_RTrackPort]]
) -> None:
    for i_port in task[0]:
        with rpr.connect(i_port['host']):
            with i_port['track'].project.make_current_project():
                set_track_midi_in(i_port['track'], i_port['port']['idx'])
    for o_port in task[1]:
        with rpr.connect(o_port['host']):
            with o_port['track'].project.make_current_project():
                set_track_midi_out(o_port['track'], o_port['port']['idx'])


def get_host_jack_ports(
    host: str
) -> ty.Tuple[ty.List[_JMidiPort], ty.List[_JMidiPort]]:
    with rpr.connect(host):
        with rpr.inside_reaper():
            a_id = RPR.NamedCommandLookup(
                '_RSd998e996a6ce8d0edf5efb3a68c86790e67cd3b4'
            )
            rpr.perform_action(a_id)
            return prs.loads('slave_ports')
