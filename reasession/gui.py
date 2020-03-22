'''
Application example using build() + return
==========================================

An application can be built if you return a widget on build(), or if you set
self.root.
'''
from IPy import IP  # type:ignore
import socket as st
import reapy as rpr
import typing as ty

from networking import send_data
from networking import DEF_HOST, MASTER_PORT, GUI_PORT
from networking import ReaperServer
from networking import IHandler
from basic_handlers import PrintHandler
from common import log
from common import SolarizedPallete as Colors
from gui_modules import basic_wrappers as bw
from gui_communicate import example_gui_info, GuiInfo
from gui_communicate import T_tracked_track_direction
from gui_communicate import T_tracked_track_type
from gui_communicate import T_tracked_track
import json as js

import kivy
from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.properties import (
    ObjectProperty, StringProperty, ListProperty, BooleanProperty
)
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.modalview import ModalView
from kivy.clock import Clock
from kivy.lang import Builder

kivy.require('1.0.7')  # type:ignore

log.enable_print()

Builder.load_file('./gui_modules/theme.kv')  # type:ignore


class Slave(BoxLayout):
    slave_address = ObjectProperty()

    def __init__(self, address: str, *args: object, **kwargs: object) -> None:
        self.slave_address = address
        super().__init__(*args, **kwargs)  # type:ignore


class SlaveDisconnectedPopup(ModalView):
    slave_ip = StringProperty()
    choice = StringProperty()
    project = ty.cast('SlaveProject', ObjectProperty())

    def __init__(
        self, project: 'SlaveProject', *args: object, **kwargs: object
    ) -> None:
        super().__init__(*args, **kwargs)  # type:ignore
        self.slave_ip = project.ip
        self.project = project

    def on_open(self) -> None:
        ...

    def close(self, option: str) -> None:
        if option == 'raise':
            self.project.connected = True
            return self.dismiss()  # type:ignore
        if option == 'choose_another':
            self.dismiss()  # type:ignore
            view = SlaveProjectRaise2Popup(self.project)
            view.open()  # type:ignore
        if option == 'leave':
            return self.dismiss()  # type:ignore

    def on_dismiss(self) -> bool:
        ...


class SlaveProjectRaise2Popup(ModalView):
    project = ty.cast('SlaveProject', ObjectProperty())
    slaves_list = ty.cast(ty.List[str], ListProperty())

    def __init__(
        self, project: 'SlaveProject', *args: object, **kwargs: object
    ) -> None:
        super().__init__(*args, **kwargs)  # type:ignore
        self.project = project
        self.slaves_list = project.slaves_list

    def on_open(self) -> None:
        ...

    def close(self, option: str) -> None:
        if option == 'raise':
            self.project.connected = True
            return self.dismiss()  # type:ignore
        if option == 'choose_another':
            self.dismiss()  # type:ignore
            view = SlaveProjectRaise2Popup(self.project)
            view.open()  # type:ignore
        if option == 'leave':
            return self.dismiss()  # type:ignore

    def on_dismiss(self) -> bool:
        ...


class SlaveProject(FloatLayout):
    name: str = StringProperty('<project name>')
    ip: str = StringProperty('127.0.0.1')
    connected: bool = BooleanProperty(False)

    def __init__(
        self,
        # slaves: ty.List[Slave],
        *args: object,
        name: str = '<project name>',
        ip: str = '127.0.0.1',
        connected: bool = False,
        **kwargs: object
    ) -> None:
        super().__init__(*args, **kwargs)  # type:ignore
        self.name = name
        self.ip = ip
        self.connected = connected
        # self.slaves_list = [sl.slave_address for sl in slaves]
        # print(self.slaves_list)

    def selected(self) -> None:
        print('pressed')
        if not self.connected:
            view = SlaveDisconnectedPopup(self)
            view.open()  # type:ignore

    def close(self) -> None:
        print('closed')
        self.connected = False


class TrackedTrack(BoxLayout):
    master_id = StringProperty()
    slave_id = StringProperty()
    master_str = StringProperty()
    slave_str = StringProperty()
    direction = ty.cast(T_tracked_track_direction, ObjectProperty())
    conn_type = ty.cast(T_tracked_track_type, ObjectProperty())

    def __init__(
        self, track_info: T_tracked_track, *args: object, **kwargs: object
    ) -> None:
        self.master_id = track_info['master_id']
        self.slave_id = track_info['slave_id']
        self.master_str = track_info['master_str']
        self.slave_str = track_info['slave_str']
        self.direction = track_info['direction']
        self.conn_type = track_info['conn_type']
        print(self.conn_type.value)
        super().__init__(*args, **kwargs)  # type:ignore


class Main(kivy.uix.floatlayout.FloatLayout, IHandler):
    '''Create a controller that receives a custom widget from the kv lang file.

    Add an action to be called from the kv lang file.
    '''
    # slaves_widget = ty.cast(BoxLayout, ObjectProperty())

    slaves = ty.cast(BoxLayout, ObjectProperty())
    slave_projects = ty.cast(BoxLayout, ObjectProperty())
    tracked_tracks = ty.cast(BoxLayout, ObjectProperty())
    gui_info = ty.cast(GuiInfo, ObjectProperty(example_gui_info))
    master_project_name = StringProperty('<master name>')
    count = 0

    def redraw_gui_from_info(self) -> None:
        print('redrawing')
        self.master_project_name = self.gui_info['master']['project_name']

        self.slaves.clear_widgets()
        for addr in self.gui_info['slave_servers']:
            self.slaves.add_widget(Slave(str(addr)))

        self.slave_projects.clear_widgets()
        self.slave_projects.height = len(self.gui_info['slave_projects']) * 50
        for slave_info in self.gui_info['slave_projects']:
            self.slave_projects.add_widget(
                SlaveProject(
                    name=slave_info['name'],
                    ip=str(slave_info['ip']),
                    connected=slave_info['connection_status']
                )
            )

        self.tracked_tracks.clear_widgets()
        self.tracked_tracks.height = len(self.gui_info['tracked_tracks']) * 50
        for track_info in self.gui_info['tracked_tracks']:
            self.tracked_tracks.add_widget(TrackedTrack(track_info))

    def can_handle(self, data_type: bytes) -> bool:
        if data_type == b'slave_list': return True
        return False

    def handle(self, data_type: bytes, data: bytes) -> bytes:
        for slave in self.slaves:
            self.slaves_wid.remove_widget(slave)
        self.slaves.clear()
        slaves = ty.cast(ty.List[str], js.loads(data, encoding='utf-8'))
        print(slaves)
        for host in slaves:
            slave = Slave()
            self.slaves.append(slave)
            self.slaves_wid.add_widget(self.slaves[-1])
            slave.slave_address.text = host
        return bytes('success', 'utf-8')

    def add_slave_project(self) -> None:
        self.count += 1
        self.slave_projects.add_widget(
            SlaveProject(slaves=self.slaves, name=str(self.count))
        )
        self.slave_projects.height = len(
            ty.cast(ty.List[SlaveProject], self.slave_projects.children)
        ) * 50


class SessionManagementApp(App):
    def build(self) -> Main:
        # return a Button() as a root widget
        main = Main()
        # main = bw.ErrorPopup('error message')
        # main.open()
        # server = ReaperServer(DEF_HOST, GUI_PORT, [PrintHandler])
        # server.register_handler(main)
        # Clock.schedule_interval(lambda dt: server.run(), 1 / 30)
        return main


if __name__ == '__main__':
    bw.load_kv()
    app = SessionManagementApp()
    app.build_config
    app.run()