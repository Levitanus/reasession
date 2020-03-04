"""Connections realization for using with Jack.

The main flow is
----------------
    - get host info
    - get jack midi ports for each host
    - match Reaper midi ports to Jack midi ports
    - match availble master ports to availble slave ports
    - connect tracks to the appropriate MIDI devices

Currently, backend do not touch Jack connections, just observe.

Attributes
----------
CONN_NAME_REGEXP : compilled regexp
    used by the 'parce_host_name(port: jack.Port)'

"""

import typing as ty
import re
import typing_extensions as te
import jack
import reapy as rpr
from reapy import reascript_api as RPR
from session_management import persistence as prs
from . import interface as iface

CONN_NAME_REGEXP = re.compile(r'(.+):(.+)')


class PortNameError(Exception):
    """Just in case jack will show unexpected name."""


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
    """Return tuple from 'jack.Port().name'.

    Parameters
    ----------
    port : jack.Port


    Returns
    -------
    ty.Tuple[str, str]
        first is host name, second is port name.
        For example: 'REAPER:Midi Out 1' will be split to
        ('REAPER', 'Midi Out 1')

    Raises
    ------
    PortNameError
        in case jack gave strange name pattern

    """
    m = re.match(CONN_NAME_REGEXP, port.name)
    if not m:
        raise PortNameError(f'strange port name: {port.name}')
    return ty.cast(ty.Tuple[str, str], m.groups())


def get_jack_ports_parametrized(want_output: bool = False
                                ) -> ty.List[_JMidiPort]:
    """Get all Reraper jack Midi in either out ports in dict.

    Parameters
    ----------
    want_output : bool, optional
        If not set — input ports will be returned

    Returns
    -------
    ty.List[_JMidiPort]
        name: str
        connection: _JConnection
            host: str
            name: str

    """
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
    """Get all Reaper jack Midi ports.

    Returns
    -------
    Tuple[ins : ty.Tuple[ty.List[_JMidiPort], ty.List[_JMidiPort]]
        See get_jack_ports_parametrized for dict info.

    """
    j_ins = get_jack_ports_parametrized()
    j_outs = get_jack_ports_parametrized(True)
    return j_ins, j_outs


def set_track_midi_out(
    track: rpr.Track, out_idx: int, out_ch: int = 0
) -> None:
    """Set Reaper track midi hardware out.

    Parameters
    ----------
    track : rpr.Track
        Description
    out_idx : int
        MIDI device id
    out_ch : int, optional
        all channels by default
    track : reapy.Track

    """
    CH_BITS = 5
    value = (out_idx << CH_BITS) + out_ch
    RPR.SetMediaTrackInfo_Value(track.id, 'I_MIDIHWOUT', value)  # type:ignore


def set_track_midi_in(track: rpr.Track, out_idx: int, out_ch: int = 0) -> None:
    """Set Reaper track midi hardware input device.

    Parameters
    ----------
    track : rpr.Track
        Description
    out_idx : int
        MIDI device id
    out_ch : int, optional
        all channels by default
    track : reapy.Track

    """
    MIDI_FLAG = 4096
    CH_BITS = 5
    value = MIDI_FLAG + (out_idx << CH_BITS) + out_ch
    RPR.SetMediaTrackInfo_Value(track.id, 'I_RECINPUT', value)  # type:ignore


def match_host_ports_parametrized(
    r_ports: ty.List[_RMidiPort],
    j_ports: ty.List[_JMidiPort],
    hostname: str,
) -> ty.List[_RHostPort]:
    """Match midi devices within ip of their connections.

    Parameters
    ----------
    r_ports : ty.List[_RMidiPort]
        idx: int
        name: str
    j_ports : ty.List[_JMidiPort]
        name: str
        connection: _JConnection
            host:str
            name:str
    hostname : str
        localhost or IPV4 address

    """
    out: ty.List[_RHostPort] = []

    def validate_name(r_port: _RMidiPort, j_port: _JMidiPort) -> bool:
        """Check if Reaper midi port is valid jack port.

        Parameters
        ----------
        r_port : _RMidiPort
        j_port : _JMidiPort

        Returns
        -------
        bool

        """
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


_HostPortsMatched = ty.Tuple[ty.List[_RHostPort], ty.List[_RHostPort]]


def match_host_ports(host: _HostInfo) -> _HostPortsMatched:
    """Match Jack and Reaper Midi ports from different hosts to simple list.

    Parameters
    ----------
    host : _HostInfo
        can be made by 'update_host_info(interface.HostInfo)'

    Returns
    -------
    Tuple[ins : _HostPortsMatched
        _RHostPort:
            host: str
            port _RMidiPort
            dest_host: str

    """
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


def match_hosts_ports(hosts: ty.Sequence[_HostInfo]
                      ) -> ty.Dict[str, _HostPortsMatched]:
    """Call math_host_ports on every host in list.

    Parameters
    ----------
    hosts : ty.Sequence[_HostInfo]

    Returns
    -------
    ty.Dict[str, _HostPortsMatched]
        key is host IP

    """
    ports: ty.Dict[str, _HostPortsMatched] = {}
    for host in hosts:
        ports[host['host']] = match_host_ports(host=host)
    return ports


def get_hosts_out_tracks(hosts: ty.Sequence[_HostInfo]
                         ) -> ty.Dict[str, ty.List[_ROutTrack]]:
    """Extract out_tracks list from host info.

    Parameters
    ----------
    hosts : ty.Sequence[_HostInfo]

    Returns
    -------
    ty.Dict[str, ty.List[_ROutTrack]]
        key is host IP

    """
    tracks = {}
    for host in hosts:
        tracks[host['host']] = host['out_tracks']
    return tracks


def get_hosts_in_tracks(hosts: ty.Sequence[_HostInfo]
                        ) -> ty.Dict[str, ty.List[rpr.Track]]:
    """Extract in_tracks list from host info.

    Parameters
    ----------
    hosts : ty.Sequence[_HostInfo]

    Returns
    -------
    ty.Dict[str, ty.List[rpr.Track]]
        key is host IP

    """
    tracks = {}
    for host in hosts:
        tracks[host['host']] = host['in_tracks']
    return tracks


def get_connection_task(
    hosts: ty.Sequence[_HostInfo]
) -> ty.Tuple[ty.List[_RTrackPort], ty.List[_RTrackPort]]:
    """Make task from _HostInfo.

    Rsult is attempted to be used in one for-loop cycle.

    Parameters
    ----------
    hosts : ty.Sequence[_HostInfo]
        Description
    hosts : Sequence[_HostInfo]

    Returns
    ------------------
    Tuple[out_tracks: _RTrackPort, in_tracks: _RTrackPort]

    """
    midi_outs: ty.List[_RTrackPort] = []
    midi_ins: ty.List[_RTrackPort] = []

    hosts_ports: ty.Dict[str, _HostPortsMatched] = match_hosts_ports(hosts)
    hosts_out_tracks: ty.Dict[str, ty.
                              List[_ROutTrack]] = get_hosts_out_tracks(hosts)
    hosts_in_tracks: ty.Dict[str, ty.List[rpr.
                                          Track]] = get_hosts_in_tracks(hosts)
    for o_host, o_tracks in hosts_out_tracks.items():
        for o_track in o_tracks:
            # str, rpr.Track
            i_host, i_track = _match_slave_track(o_track, hosts_in_tracks)
            # !UNCLEAN lists will be modified!
            _pop_out_port(hosts_ports, o_host, i_host, o_track, midi_outs)
            # !UNCLEAN lists will be modified!
            _pop_in_ports(hosts_ports, i_host, i_track, midi_ins)

    return midi_outs, midi_ins


def _pop_in_ports(
    hosts_ports: ty.Dict[str, _HostPortsMatched], i_host: str,
    i_track: rpr.Track, midi_ins: ty.List[_RTrackPort]
) -> None:
    """Pop reaper midi port from host info and put into the midi_ins.

    Parameters
    ----------
    hosts_ports : ty.Dict[str, _HostPortsMatched]
    i_host : str
        IP or lovalhost
    i_track : rpr.Track
    midi_ins : ty.List[_RTrackPort]
        lost to insert the port

    """
    assigned = False
    miss_in_ports_msg = "not enough in ports for host '%s'"
    for idx, i_port in enumerate(hosts_ports[i_host][0]):
        if i_port['dest_host'] == 'localhost':
            midi_ins.append(
                _RTrackPort(
                    host=i_host,
                    track=i_track,
                    port=hosts_ports[i_host][0].pop(idx)['port']
                )
            )
            assigned = True
            break
    if not assigned:
        raise iface.ConnectionsError(miss_in_ports_msg % i_host)


def _pop_out_port(
    hosts_ports: ty.Dict[str, _HostPortsMatched], o_host: str, i_host: str,
    o_track: _ROutTrack, midi_outs: ty.List[_RTrackPort]
) -> None:
    """Pop reaper midi port from host info and put into the midi_outs.

    Parameters
    ----------
    hosts_ports : ty.Dict[str, _HostPortsMatched]
    o_host : str
        IP or localhost
    i_host : str
        IP or localhost
    o_track : _ROutTrack
        master track with slave info
    midi_outs : ty.List[_RTrackPort]
        list to insert the port

    """
    miss_out_ports_msg = "not enough out ports for host '%s'"
    assigned = False
    for idx, o_port in enumerate(hosts_ports[o_host][1]):
        if o_port['dest_host'] == i_host:
            r_o_port = _RTrackPort(
                host=o_host,
                track=o_track['track'],
                port=hosts_ports[o_host][1].pop(idx)['port']
            )
            midi_outs.append(r_o_port)
            assigned = True
            break
    if not assigned:
        raise iface.ConnectionsError(miss_out_ports_msg % i_host)


def _match_slave_track(
    o_track: _ROutTrack, hosts_in_tracks: ty.Dict[str, ty.List[rpr.Track]]
) -> ty.Tuple[str, rpr.Track]:
    """Get slave track from the slave host info.

    Warning
    -------
    slave track will be poped from list.

    Parameters
    ----------
    o_track : _ROutTrack
        master track with slave info
    hosts_in_tracks : ty.Dict[str, ty.List[rpr.Track]]

    """
    s_track = o_track['slave']['track']
    assigned = False
    i_host = o_track['slave']['host']
    i_tracks = hosts_in_tracks[i_host]
    for idx, i_track in enumerate(i_tracks):
        if s_track == i_track:
            assigned = True
            i_track = i_tracks.pop(idx)
            break
    if not assigned:
        raise iface.ConnectionsError(
            "can't find track {n} in project {p} at {s}".format(
                n=s_track.name, p=s_track.project, s=i_host
            )
        )
    #  pylint: disable=W0631
    return i_host, i_track
    #  pylint: enable=W0631


def connect_by_task(
    task: ty.Tuple[ty.List[_RTrackPort], ty.List[_RTrackPort]]
) -> None:
    """Make a final connection of all tracks.

    Parameters
    ----------
    task : ty.Tuple[ty.List[_RTrackPort], ty.List[_RTrackPort]]
        see 'get_connections_task(hosts)'

    """
    for i_port in task[0]:
        with rpr.connect(i_port['host']):
            with i_port['track'].project.make_current_project():
                set_track_midi_in(i_port['track'], i_port['port']['idx'])
    for o_port in task[1]:
        with rpr.connect(o_port['host']):
            with o_port['track'].project.make_current_project():
                set_track_midi_out(o_port['track'], o_port['port']['idx'])


def get_host_jack_ports(
    host: ty.Optional[str] = None
) -> ty.Tuple[ty.List[_JMidiPort], ty.List[_JMidiPort]]:
    """Return all Jack midi ports of Reaper on the specified host.

    Note
    ----
    reascript 'Levitanus: (session_management) get_system_jack_ports'
    has to be registered in action editor.

    Parameters
    ----------
    host : ty.Optional[str], optional
        'localhost' or IPV4 address

    No Longer Returned
    ------------------
    jack_in_ports: _JMidiPort
    jack_out_ports _JMidiPort

    """
    if host == 'localhost':
        host = None
    with rpr.connect(host):
        with rpr.inside_reaper():
            a_id: int = RPR.NamedCommandLookup(
                '_RSc3a0868bee74abaf333ac661af9a4a27257c37c1'
            )
            rpr.perform_action(a_id)
            ports = prs.loads('slave_ports')
            # print(ports)
            return ports


def get_host_midi_ports(
    host: ty.Optional[str] = None
) -> ty.Tuple[ty.List[_RMidiPort], ty.List[_RMidiPort]]:
    """Get all MIDI devices of the particular host.

    Parameters
    ----------
    host : ty.Optional[str], optional
        'localhost' or IPV4 address

    No Longer Returned
    ------------------
    jack_in_ports: _JMidiPort
    jack_out_ports _JMidiPort

    """
    if host == 'localhost':
        host = None

    ins, outs = [], []
    with rpr.connect(host):
        with rpr.inside_reaper():
            for i, port in enumerate(rpr.midi.get_input_names()):
                ins.append(_RMidiPort(idx=i, name=port))
            for i, port in enumerate(rpr.midi.get_output_names()):
                outs.append(_RMidiPort(idx=i, name=port))
    return ins, outs


def update_host_info(hosts: ty.List[iface.HostInfo]) -> ty.List[_HostInfo]:
    """Make backend-specific host info from the given one.

    Parameters
    ----------
    hosts : ty.List[iface.HostInfo]
        ip and list of in and out tracks

    Returns
    -------
    ty.List[_HostInfo]
        ip, list of tracks and list of midi ports

    """
    hosts_new: ty.List[_HostInfo] = []
    for host in hosts:
        jack_in_ports, jack_out_ports = get_host_jack_ports(host['host'])
        reaper_in_ports, reaper_out_ports = get_host_midi_ports(host['host'])
        hosts_new.append(
            _HostInfo(
                host=host['host'],
                in_tracks=host['in_tracks'],
                out_tracks=host['out_tracks'],
                jack_in_ports=jack_in_ports,
                jack_out_ports=jack_out_ports,
                reaper_in_ports=reaper_in_ports,
                reaper_out_ports=reaper_out_ports,
            )
        )
    return hosts_new


class Connector(iface.Connector):
    """Concrete Connector realization.

    Accepts HostInfo and connects tracks by Jack backend

    Init Parameters
    ---------------
    hosts : List[HostInfo]
            see interface.HostInfo

    """

    def connect_all(self) -> None:
        """Call by the class user.

        Connect all given via HostInfo tracks to each other, using Jack backend

        Raises
        ------
        sessioin_management.connections.interface.ConnectionsError

        """
        host_info = update_host_info(self.hosts)
        task = get_connection_task(host_info)
        connect_by_task(task)
