import typing as ty
import typing_extensions as te
import re
from abc import ABC, abstractmethod
import reapy as rpr
from reapy import reascript_api as RPR
import jack
import warnings
from session_management import persistence

from IPy import IP

CONN_NAME_REGEXP = re.compile(r'(.+):(.+)')


class PortNameError(Exception):
    pass


def parce_port_name(port: jack.Port) -> ty.Tuple[str, str]:
    m = re.match(CONN_NAME_REGEXP, port.name)
    if not m:
        raise PortNameError(f'strange port name: {port.name}')
    return ty.cast(ty.Tuple[str, str], m.groups())


class HardwarePorts:
    def __init__(self, is_master: bool = True) -> None:
        self._is_master = is_master
        self.client = jack.Client('observer')
        self._reaper_ports: ty.List[JackPort] = self.update_reaper_ports()

    def update_reaper_ports(self) -> ty.List['JackPort']:
        reaper_ports: ty.List['JackPort'] = []
        is_output, is_input = self._is_master, not self._is_master
        conn_type: ty.Type[JackPort] = SlaveJackPort
        if not self._is_master:
            conn_type = SystemJackPort
        for port in ty.cast(
            ty.List[jack.MidiPort],
            self.client.get_ports(
                name_pattern='REAPER',
                is_midi=True,
                is_output=is_output,
                is_input=is_input
            )
        ):
            connections = ty.cast(
                ty.List[jack.MidiPort], self.client.get_all_connections(port)
            )
            reaper_ports.append(conn_type(port, connections))
        return reaper_ports

    def __repr__(self) -> str:
        if not self._reaper_ports:
            return 'No MIDI Connections'
        master = 'to slaves'
        if not self._is_master:
            master = 'from system'
        out = f'HardwarePorts object at <{id(self)}>\n' +\
            f'    REAPER MIDI connections {master}:'
        for port in self._reaper_ports:
            out += f'\n        {port}'
        return out


class JackPortError(Exception):
    def __init__(
        self, port: jack.MidiPort, connections: ty.List[jack.MidiPort]
    ) -> None:
        msg = \
            f'too many connections to slaves from port "{port}": {connections}'
        super().__init__(msg)


class JackPort(ABC):
    connection: ty.Optional[jack.MidiPort]

    def __init__(
        self, port: jack.MidiPort, connections: ty.List[jack.MidiPort]
    ) -> None:
        self.port = port
        self._conn_name_regexp = CONN_NAME_REGEXP
        self.connection = self.construct_connection(connections)

    @abstractmethod
    def construct_connection(self, connections: ty.List[jack.MidiPort]
                             ) -> ty.Optional[jack.MidiPort]:
        raise NotImplementedError

    @abstractmethod
    def __repr__(self) -> str:
        raise NotImplementedError


class SlaveJackPort(JackPort):
    def construct_connection(self, connections: ty.List[jack.MidiPort]
                             ) -> ty.Optional[jack.MidiPort]:
        if not connections:
            return None
        valid: ty.List[jack.MidiPort] = []
        for conn in connections:
            host, name = parce_port_name(conn)
            try:
                IP(host)
                valid.append(conn)
            except ValueError:
                if host == 'REAPER':
                    valid.append(conn)
                continue

        if len(valid) > 1:
            raise JackPortError(self.port, valid)
        if not valid:
            warnings.warn(Warning(f'no valid ports found'))
            return None
        return valid[0]

    def __repr__(self) -> str:
        conn = 'None'
        if self.connection:
            conn = self.connection.name
        return f'{self.port.name} -> {conn}'


class SystemJackPort(JackPort):
    def construct_connection(self, connections: ty.List[jack.MidiPort]
                             ) -> ty.Optional[jack.MidiPort]:
        if not connections:
            return None
        valid: ty.List[jack.MidiPort] = []
        for conn in connections:
            host, name = parce_port_name(conn)
            if host not in ('system', 'REAPER'):
                continue
            valid.append(conn)
        if len(valid) > 1:
            raise JackPortError(self.port, valid)
        if not valid:
            warnings.warn(Warning(f'no valid ports found'))
            return None
        return valid[0]

    def __repr__(self) -> str:
        conn = 'None'
        if self.connection:
            conn = self.connection.name
        return f'{conn} -> {self.port.name}'


_PortDump = te.TypedDict('_PortDump', {'host': str, 'name': str, 'uuid': str})


class JackPortDump:
    port: _PortDump
    connection: ty.Optional[_PortDump]

    def __init__(self, port: JackPort) -> None:
        host, name = parce_port_name(port.port)
        self.port = {'host': host, 'name': name, 'uuid': port.port.uuid}
        if not port.connection:
            self.connection = None
            return
        host, name = parce_port_name(port.connection)
        self.connection = {
            'host': host,
            'name': name,
            'uuid': port.connection.uuid
        }

    def __repr__(self) -> str:
        return '<{m}.JackPortDump (port: {p}, connection: {c})>'.format(
            m=self.__module__, p=self.port, c=self.connection
        )


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


_ReaperPort = te.TypedDict('_ReaperPort', {'idx': int, 'name': str})

# class Session:
#     def get_out_tracks(
#         self
#     ) -> ty.Tuple[ty.List[rpr.Track], ty.List[rpr.Track], ty.List[str]]:
#         ...

# class Connector:
#     def __init__(self, session: Session) -> None:
#         self.session = session

#     def get_active_slave_tracks(
#         self
#     ) -> ty.Tuple[ty.List[rpr.Track], ty.List[rpr.Track], ty.List[str]]:
#         m_tracks, s_tracks, s_hosts = self.session.get_out_tracks()
#         o_m_tracks: ty.List[rpr.Track] = []
#         o_s_tracks: ty.List[rpr.Track] = []
#         o_s_hosts: ty.List[str] = []
#         for m_track, s_track, s_host in zip(m_tracks, s_tracks, s_hosts):
#             with rpr.connect(s_host):
#                 with s_track.project.make_current_project():
#                     if rpr.Project().name == s_track.project.name:
#                         o_m_tracks.append(m_track)
#                         o_s_tracks.append(s_track)
#                         o_s_hosts.append(s_host)
#         return o_m_tracks, o_s_tracks, o_s_hosts

#     def get_slave_in_port(self, host: str) -> _ReaperPort:
#         with rpr.connect(host):
#             with rpr.inside_reaper():
#                 rpr.perform_action(
#                     RPR.NamedCommandLookup('get_system_jack_ports')
#                 )
#                 jack_ports = persistence.loads('slave_ports')

#     def get_slaves_in_ports(self,
#                             s_hosts: ty.List[str]) -> ty.List[_ReaperPort]:
#         ports = {}
#         ports_used = {}
#         out = []
#         for host in set(s_hosts):
#             ports[host] = self.get_slave_in_port(host)
#             ports_used[host] = 0
#         for host in s_hosts:
#             out.append(ports[host][ports_used[host]])
#             ports_used[host] += 1

#     def connect_all(self) -> None:
#         m_tracks, s_tracks, s_hosts = self.get_active_slave_tracks()
#         s_in_ports = self.get_slaves_in_ports(s_hosts)
#         m_outs = self.get_master_ports(m_tracks, s_hosts)
#         for m_track, m_out, s_host, s_track, s_in in zip(
#             m_tracks, m_outs, s_hosts, s_tracks, s_in_ports
#         ):
#             self.connect(
#                 m_track=m_tracks,
#                 m_out=m_out,
#                 s_host=s_host,
#                 s_track=s_track,
#                 s_in=s_in
#             )

#     def connect(
#         self, m_track: rpr.Track, m_out: _ReaperPort, s_host: str,
#         s_track: rpr.Track, s_in: _ReaperPort
#     ) -> None:
#         pass

_JConection = te.TypedDict('_JConection', {'host': str, 'name': str})
_JMidiPort = te.TypedDict(
    '_JMidiPort', {
        'name': str,
        'connection': _JConection
    }
)
_RMidiPort = te.TypedDict('_RMidiPort', {'idx': int, 'name': str})
_RSlaveTrack = te.TypedDict('_RSlaveTrack', {'host': str, 'track': rpr.Track})
_ROutTrack = te.TypedDict(
    '_ROutTrack', {
        'track': rpr.Track,
        'slave': _RSlaveTrack
    }
)

_HostInfo = te.TypedDict(
    '_HostInfo', {
        'host': str,
        'reaper_in_ports': ty.List[_RMidiPort],
        'jack_in_ports': ty.List[_JMidiPort],
        'in_tracks': ty.List[rpr.Track],
        'reaper_out_ports': ty.List[_RMidiPort],
        'jack_out_ports': ty.List[_JMidiPort],
        'out_tracks': ty.List[_ROutTrack]
    }
)
_RTrackPort = te.TypedDict(
    '_RTrackPort', {
        'host': str,
        'track': rpr.Track,
        'port': _RMidiPort
    }
)
_RHostPort = te.TypedDict(
    '_RHostPort', {
        'host': str,
        'port': _RMidiPort,
        'dest_host': str,
    }
)


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
