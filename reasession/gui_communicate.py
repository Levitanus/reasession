import typing as ty
import typing_extensions as te
import IPy as ipy
from enum import Enum

from networking import IHandler
from networking import ReaperServer
from networking import GUI_PORT, MASTER_PORT, DEF_HOST
from networking import send_data
from networking import encode_data
from basic_handlers import PrintHandler
from slaves import Slaves


class GuiHandler(IHandler):
    def __init__(self, parent: 'GuiServer') -> None:
        self._handlers: ty.Dict[bytes, ty.Callable[[bytes], bytes]] = {
            b'gui_start': self._gui_start,
        }
        self._parent = parent

    def can_handle(self, data_type: bytes) -> bool:
        if data_type in self._handlers:
            return True
        return False

    def handle(self, data_type: bytes, data: bytes) -> bytes:
        return self._handlers[data_type](data)

    def _gui_start(self, data: bytes) -> bytes:
        return encode_data(self._parent.update_gui_info())


class GuiServer:
    def __init__(self, slaves: Slaves) -> None:
        self._server = ReaperServer(DEF_HOST, MASTER_PORT, [PrintHandler])
        self._gui_handler = GuiHandler(self)
        self._server.register_handler(self._gui_handler)
        self._slaves = slaves

    def run(self) -> None:
        return self._server.run()

    def at_exit(self) -> None:
        return self._server.at_exit()

    def uptade_gui(self) -> None:
        send_data(
            'gui_update', self.update_gui_info(), host=DEF_HOST, port=GUI_PORT
        )

    def update_gui_info(self) -> ty.Dict[str, ty.List[str]]:
        return {'slaves': self._slaves.active_slaves_list()}


T_slave_servers = ty.List[ipy.IP]
T_SlaveProject = te.TypedDict(
    'T_SlaveProject', {
        'ip': ipy.IP,
        'name': str,
        'connection_status': bool,
    }
)
T_slave_projects = ty.List[T_SlaveProject]


class T_tracked_track_direction(Enum):
    to_slave = object()
    to_master = object()


class T_tracked_track_type(Enum):
    midi = 'midi'
    audio = 'audio'


T_tracked_track = te.TypedDict(
    'T_tracked_track', {
        'master_id': str,
        'master_str': str,
        'slave_id': str,
        'slave_str': str,
        'direction': T_tracked_track_direction,
        'conn_type': T_tracked_track_type,
    }
)
T_master = te.TypedDict('T_master', {'project_name': str, 'project_path': str})

GuiInfo = te.TypedDict(
    'GuiInfo', {
        'slave_servers': T_slave_servers,
        'slave_projects': ty.List[T_SlaveProject],
        'tracked_tracks': ty.List[T_tracked_track],
        'master': T_master,
    }
)

example_gui_info = GuiInfo(
    slave_servers=[
        ipy.IP('127.0.0.1'),
        ipy.IP('192.168.1.2'),
        ipy.IP('192.168.1.3')
    ],
    slave_projects=[
        T_SlaveProject(
            ip=ipy.IP('127.0.0.1'), name='slave1', connection_status=True
        ),
        T_SlaveProject(
            ip=ipy.IP('192.168.1.2'), name='slave2', connection_status=False
        )
    ],
    tracked_tracks=[
        T_tracked_track(
            master_id='master_track_id',
            master_str='015:violins I midi',
            slave_id='slave_track_id',
            slave_str='008:violins I recieve',
            direction=T_tracked_track_direction.to_slave,
            conn_type=T_tracked_track_type.midi
        ),
        T_tracked_track(
            master_id='master_track_id',
            master_str='016:violins II midi',
            slave_id='slave_track_id',
            slave_str='009:violins II recieve',
            direction=T_tracked_track_direction.to_master,
            conn_type=T_tracked_track_type.audio
        )
    ],
    master={
        'project_name': 'my_master_project',
        'project_path': 'master/path/string/my_master_project.RPP'
    }
)

T_track_info = te.TypedDict('T_track_info', {'name': str, 'id': str})
