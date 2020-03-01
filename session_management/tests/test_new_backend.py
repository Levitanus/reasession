from socket import socket
import typing as ty
import pytest as pt
import reapy as rpr
from reapy import reascript_api as RPR
from IPy import IP
from ..connections import backend as bck
import mock


class Call:
    def __init__(
        self, module: str, class_: str, method: str,
        params: ty.Dict[str, object]
    ) -> None:
        self.module = module
        self.class_ = class_
        self.method = method
        self.params = params

    def __repr__(self) -> str:
        return '{m}.{c}.{mt}: {p}'.format(
            m=self.module, c=self.class_, mt=self.method, p=self.params
        )


class CallsObserver:
    logs: ty.List[ty.List[Call]] = []

    def __init__(self, log_list: ty.List[Call]) -> None:
        self.__class__.logs.append(log_list)

    @classmethod
    def push(cls, call: Call) -> None:
        for log in cls.logs:
            log.append(call)


class MonkeyTrack():
    def __init__(
        self,
        id: ty.Union[str, int] = None,
        project: ty.Optional[rpr.Project] = None
    ) -> None:
        self.id = id
        self.project = project

    def __repr__(self) -> str:
        return f'(MediaTrack id={self.id}, project={self.project})'

    def __eq__(self, other: object) -> bool:
        # print('cmp called')
        if not isinstance(other, MonkeyTrack):
            # raise RuntimeError('not equal')
            return False
        if other.id == self.id:
            return True
        # raise RuntimeError('not equal')
        return False


class MonkeyProject():
    def __init__(self, id: ty.Optional[str] = None, index: int = -1) -> None:
        self.id = id
        self.index = index
        self.name = 'defaultname'

    def __repr__(self) -> str:
        return f'(ReaProject id={self.id}, index={self.index}'

    def make_current_project(self) -> ty.ContextManager:
        class CM:
            def __enter__(self) -> None:
                return None

            def __exit__(self, exc_type, exc_val, exc_tb):
                return

        return CM()

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, MonkeyProject):
            return False
        if self.id == other.id:
            return True
        if self.name == other.name:
            return True
        return False


def get_test_data(
) -> ty.Tuple[bck._HostInfo, bck._HostInfo, ty.List[bck._RTrackPort], ty.
              List[bck._RTrackPort]]:
    master: bck._HostInfo = dict(
        host='localhost',
        reaper_in_ports=[
            dict(idx=0, name='system:midi_capture_1'),
            dict(idx=1, name='system:midi_capture_2'),
            dict(idx=2, name='MIDI Input 3'),
            dict(idx=3, name='MIDI Input 4'),
            dict(idx=4, name='MIDI Input 5'),
        ],
        jack_in_ports=[
            dict(
                name='MIDI Input 1',
                connection=dict(host='system', name='midi_capture_1')
            ),
            dict(
                name='MIDI Input 2',
                connection=dict(host='system', name='midi_capture_2')
            ),
            dict(
                name='MIDI Input 3',
                connection=dict(host='REAPER', name='MIDI Output 6')
            ),
            dict(
                name='MIDI Input 4',
                connection=dict(host='192.168.2.2', name='midi_from_slave_1')
            ),
        ],
        in_tracks=[
            rpr.Track(
                id='slave_track_1', project=rpr.Project(id='slave_project_1')
            )
        ],
        reaper_out_ports=[
            dict(idx=0, name='system:midi_playback_1'),
            dict(idx=1, name='system:midi_playback_2'),
            dict(idx=2, name='MIDI Output 3'),
            dict(idx=3, name='MIDI Output 4'),
            dict(idx=4, name='MIDI Output 5'),
            dict(idx=5, name='MIDI Output 6'),
            dict(idx=6, name='MIDI Output 7'),
        ],
        jack_out_ports=[
            dict(
                name='MIDI Output 1',
                connection=dict(host='system', name='midi_playback_1')
            ),
            dict(
                name='MIDI Output 2',
                connection=dict(host='system', name='midi_playback_2')
            ),
            dict(
                name='MIDI Output 3',
                connection=dict(host='192.168.2.2', name='midi_to_slave_1')
            ),
            dict(
                name='MIDI Output 4',
                connection=dict(host='192.168.2.2', name='midi_to_slave_2')
            ),
            dict(
                name='MIDI Output 5',
                connection=dict(host='192.168.2.2', name='midi_to_slave_3')
            ),
            dict(
                name='MIDI Output 6',
                connection=dict(host='REAPER', name='MIDI Input 3')
            ),
        ],
        out_tracks=[
            dict(
                track=rpr.Track(
                    id='master_track_1',
                    project=rpr.Project(id='master_project')
                ),
                slave=dict(
                    host='192.168.2.2',
                    track=rpr.Track(
                        id='slave_track_2',
                        project=rpr.Project(id='slave_project_2')
                    )
                )
            ),
            dict(
                track=rpr.Track(
                    id='master_track_2',
                    project=rpr.Project(id='master_project')
                ),
                slave=dict(
                    host='192.168.2.2',
                    track=rpr.Track(
                        id='slave_track_3',
                        project=rpr.Project(id='slave_project_2')
                    )
                )
            ),
            dict(
                track=rpr.Track(
                    id='master_track_3',
                    project=rpr.Project(id='master_project')
                ),
                slave=dict(
                    host='192.168.2.2',
                    track=rpr.Track(
                        id='slave_track_4',
                        project=rpr.Project(id='slave_project_3')
                    )
                )
            ),
            dict(
                track=rpr.Track(
                    id='master_track_4',
                    project=rpr.Project(id='master_project')
                ),
                slave=dict(
                    host='localhost',
                    track=rpr.Track(
                        id='slave_track_1',
                        project=rpr.Project(id='slave_project_1')
                    )
                )
            ),
        ],
    )
    slave: bck._HostInfo = dict(
        host='192.168.2.2',
        reaper_in_ports=[
            dict(idx=0, name='system:midi_capture_1'),
            dict(idx=1, name='system:midi_capture_2'),
            dict(idx=2, name='system:midi_capture_3'),
            dict(idx=3, name='system:midi_capture_4'),
            dict(idx=4, name='MIDI Input 5'),
        ],
        jack_in_ports=[
            dict(
                name='MIDI Input 1',
                connection=dict(host='system', name='midi_capture_1')
            ),
            dict(
                name='MIDI Input 2',
                connection=dict(host='system', name='midi_capture_2')
            ),
            dict(
                name='MIDI Input 3',
                connection=dict(host='system', name='midi_capture_3')
            ),
            dict(
                name='MIDI Input 4',
                connection=dict(host='system', name='midi_capture_4')
            ),
        ],
        in_tracks=[
            rpr.Track(
                id='slave_track_2', project=rpr.Project(id='slave_project_2')
            ),
            rpr.Track(
                id='slave_track_3', project=rpr.Project(id='slave_project_2')
            ),
            rpr.Track(
                id='slave_track_4', project=rpr.Project(id='slave_project_3')
            )
        ],
        reaper_out_ports=[
            dict(idx=0, name='system:midi_playback_1'),
            dict(idx=1, name='MIDI Output 2'),
        ],
        jack_out_ports=[
            dict(
                name='MIDI Output 1',
                connection=dict(host='system', name='midi_playback_1')
            )
        ],
        out_tracks=[],
    )
    midi_outs: ty.List[bck._RTrackPort] = [
        dict(
            host='localhost',
            track=rpr.Track(
                id='master_track_1', project=rpr.Project(id='master_project')
            ),
            port=dict(idx=2, name='MIDI Output 3'),
        ),
        dict(
            host='localhost',
            track=rpr.Track(
                id='master_track_2', project=rpr.Project(id='master_project')
            ),
            port=dict(idx=3, name='MIDI Output 4'),
        ),
        dict(
            host='localhost',
            track=rpr.Track(
                id='master_track_3', project=rpr.Project(id='master_project')
            ),
            port=dict(idx=4, name='MIDI Output 5'),
        ),
        dict(
            host='localhost',
            track=rpr.Track(
                id='master_track_4', project=rpr.Project(id='master_project')
            ),
            port=dict(idx=5, name='MIDI Output 6'),
        ),
    ]
    midi_ins: ty.List[bck._RTrackPort] = [
        dict(
            host='localhost',
            track=rpr.Track(
                id='slave_track_1', project=rpr.Project(id='slave_project_1')
            ),
            port=dict(idx=2, name='MIDI Input 3')
        ),
        dict(
            host='192.168.2.2',
            track=rpr.Track(
                id='slave_track_2', project=rpr.Project(id='slave_project_2')
            ),
            port=dict(idx=0, name='system:midi_capture_1'),
        ),
        dict(
            host='192.168.2.2',
            track=rpr.Track(
                id='slave_track_3', project=rpr.Project(id='slave_project_2')
            ),
            port=dict(idx=1, name='system:midi_capture_2'),
        ),
        dict(
            host='192.168.2.2',
            track=rpr.Track(
                id='slave_track_4', project=rpr.Project(id='slave_project_3')
            ),
            port=dict(idx=2, name='system:midi_capture_3'),
        ),
    ]
    return master, slave, midi_outs, midi_ins


def monkey_connect(self, *args, **kwargs) -> None:
    pass


def monkey_get_out_tracks(
    t_master
) -> ty.Tuple[ty.List[rpr.Track], ty.List[rpr.Track], ty.List[str]]:
    m_tracks: ty.List[rpr.Track] = []
    s_tracks: ty.List[rpr.Track] = []
    s_hosts: ty.List[str] = []
    for track in t_master['out_tracks']:
        m_tracks.append(track['track'])
        s_tracks.append(track['slave']['track'])
        s_hosts.append(track['slave']['host'])
    out = m_tracks, s_tracks, s_hosts
    # print(out)
    return out


class MonkeyClient:
    def __init___(self, port, host='localhost'):
        self.port, self.host = port, host

    def request(self, function, input=None):
        return 'monkey_client_request'


# def test_connect_all(monkeypatch):
#     session = bck.Session()
#     monkeypatch.setattr(rpr, 'Track', MonkeyTrack)
#     monkeypatch.setattr(rpr, 'Project', MonkeyProject)
#     t_master, t_slave = get_test_data()
#     monkeypatch.setattr(
#         session, 'get_out_tracks', lambda: monkey_get_out_tracks(t_master)
#     )
#     connector = bck.Connector(session)
#     monkeypatch.setattr(
#         connector, 'connect',
#         lambda *args, **kwargs: monkey_connect(connector, args, kwargs)
#     )

#     log: ty.List[Call] = []
#     CallsObserver(log)
#     monkeypatch.setattr(rpr.tools.network.client, 'Client', MonkeyClient)
#     monkeypatch.setattr(socket, 'connect', lambda host, port: None)
#     # monkeypatch.setattr(
#     #     rpr.connect, '__exit__', lambda exc_type, exc_value, traceback: None
#     # )
#     connector.connect_all()
#     print(log[0])
#     assert log[0].method == 'connect'
#     assert log[0].params == dict(
#         m_track=t_master.out_tracks[0],
#         m_out=t_master.reaper_out_ports[5],
#         s_host='localhost',
#         s_track=t_master.in_tracks[0],
#         s_in=t_master.reaper_in_ports[2]
#     )


def test_get_connection_task(monkeypatch):
    monkeypatch.setattr(rpr, 'Track', MonkeyTrack)
    monkeypatch.setattr(rpr, 'Project', MonkeyProject)
    t_master, t_slave, t_midi_outs, t_midi_ins = get_test_data()
    r_midi_outs, r_midi_ins = bck.get_connection_task([t_master, t_slave])

    assert t_midi_ins == r_midi_ins
    assert t_midi_outs == r_midi_outs


# @pt.mark.skip
def test_match_host_ports(monkeypatch):
    monkeypatch.setattr(rpr, 'Track', MonkeyTrack)
    monkeypatch.setattr(rpr, 'Project', MonkeyProject)
    t_host = dict(
        host='localhost',
        reaper_in_ports=[
            dict(idx=0, name='system:midi_capture_1'),
            dict(idx=2, name='MIDI Input 3'),
            dict(idx=3, name='MIDI Input 4'),
            dict(idx=4, name='MIDI Input 5'),
        ],
        jack_in_ports=[
            dict(
                name='MIDI Input 1',
                connection=dict(host='system', name='midi_capture_1')
            ),
            dict(
                name='MIDI Input 3',
                connection=dict(host='REAPER', name='MIDI Output 6')
            ),
            dict(
                name='MIDI Input 4',
                connection=dict(host='192.168.2.2', name='midi_from_slave_1')
            ),
        ],
        reaper_out_ports=[
            dict(idx=0, name='system:midi_playback_1'),
            dict(idx=2, name='MIDI Output 3'),
            dict(idx=5, name='MIDI Output 6'),
        ],
        jack_out_ports=[
            dict(
                name='MIDI Output 1',
                connection=dict(host='system', name='midi_playback_1')
            ),
            dict(
                name='MIDI Output 3',
                connection=dict(host='192.168.2.2', name='midi_to_slave_1')
            ),
            dict(
                name='MIDI Output 6',
                connection=dict(host='REAPER', name='MIDI Input 3')
            ),
        ],
    )
    t_output = (
        [
            dict(
                host='localhost',
                port=dict(idx=2, name='MIDI Input 3'),
                dest_host='localhost',
            ),
            dict(
                host='localhost',
                port=dict(idx=3, name='MIDI Input 4'),
                dest_host='192.168.2.2',
            )
        ],
        [
            dict(
                host='localhost',
                port=dict(idx=2, name='MIDI Output 3'),
                dest_host='192.168.2.2',
            ),
            dict(
                host='localhost',
                port=dict(idx=5, name='MIDI Output 6'),
                dest_host='localhost',
            )
        ],
    )
    assert bck.match_host_ports(t_host) == t_output


@mock.patch('reapy.Project')
@mock.patch('reapy.Track')
@mock.patch('reapy.connect')
@mock.patch('session_management.connections.backend.set_track_midi_in')
@mock.patch('session_management.connections.backend.set_track_midi_out')
def test_connect(
    set_track_midi_out, set_track_midi_in, monkey_connect, MonkeyTrack,
    MonkeyProject
):
    # t_master, t_slave, t_midi_outs, t_midi_ins = get_test_data()
    # task = bck.get_connection_task([t_master, t_slave])
    track = rpr.Track(
        id='slave_track_2', project=rpr.Project(id='slave_project_2')
    )
    task = (
        [
            dict(
                host='192.168.2.2',
                track=track,
                port=dict(idx=2, name='system:midi_capture_3'),
            ),
        ], []
    )
    bck.connect_by_task(task)
    monkey_connect.assert_called_with('192.168.2.2')
    track.project.make_current_project.assert_called()
    set_track_midi_in.assert_called_with(track, 2)

    track = rpr.Track(
        id='master_track_1', project=rpr.Project(id='master_project')
    )

    task = (
        [], [
            dict(
                host='localhost',
                track=rpr.Track(
                    id='master_track_1',
                    project=rpr.Project(id='master_project')
                ),
                port=dict(idx=3, name='MIDI Output 4'),
            ),
        ]
    )
    bck.connect_by_task(task)
    monkey_connect.assert_called_with('localhost')
    track.project.make_current_project.assert_called()
    set_track_midi_out.assert_called_with(track, 3)
