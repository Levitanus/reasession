'''
Application example using build() + return
==========================================

An application can be built if you return a widget on build(), or if you set
self.root.
'''
from IPy import IP
import socket as st

from networking import send_data
from networking import DEF_HOST, MASTER_PORT, GUI_PORT
from networking import ReaperServer
from networking import IHandler
from basic_handlers import PrintHandler
from common import log
import json as js

import kivy
kivy.require('1.0.7')

from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.properties import ObjectProperty, StringProperty, ListProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock

log.enable_print()


class Slave(BoxLayout):
    slave_address = ObjectProperty()
    conn_status = ObjectProperty()
    projects = ObjectProperty()

    def valiadate(self):
        text = self.slave_address.text
        if not self._valiadate_ip(text):
            return self._valiadate_fail()
            print(text)
        try:
            recv = send_data('ping', 'ping', text, port=MASTER_PORT)
        except st.timeout:
            return self._valiadate_fail()
        except ConnectionRefusedError:
            return self._valiadate_fail()
        if str(recv.strip()) == 'success':
            print('right')
            self.conn_status.text = 'connected'

    def _valiadate_fail(self):
        self.conn_status.text = 'not connected'

    def _valiadate_ip(self, text):
        a = text.split('.')
        if len(a) != 4:
            return False
        try:
            IP(text)
            print(text)
            return True
        except ValueError:
            return False
        except BrokenPipeError:
            return False


class Slaves(kivy.uix.floatlayout.FloatLayout, IHandler):
    '''Create a controller that receives a custom widget from the kv lang file.

    Add an action to be called from the kv lang file.
    '''
    slaves_wid = ObjectProperty()

    slave = ObjectProperty()
    slaves = ListProperty()

    def can_handle(self, data_type: bytes) -> bool:
        if data_type == b'slave_list': return True
        return False

    def handle(self, data_type: bytes, data: bytes) -> bytes:
        for slave in self.slaves:
            self.slaves_wid.remove_widget(slave)
        self.slaves.clear()
        slaves = js.loads(data, encoding='utf-8')
        print(slaves)
        for host in slaves:
            slave = Slave()
            self.slaves.append(slave)
            self.slaves_wid.add_widget(self.slaves[-1])
            slave.slave_address.text.set(host)
        return bytes('success', 'utf-8')

    def do_action(self):
        self.label_wid.text = 'My label after button press'
        self.info = 'New info text'

    def action(self):
        self.slaves.append(Slave())
        self.slaves_wid.add_widget(self.slaves[-1])


class SessionManagementApp(App):
    def build(self):
        # return a Button() as a root widget
        return Slaves()


if __name__ == '__main__':
    server = ReaperServer(DEF_HOST, GUI_PORT, [PrintHandler, Slaves])

    Clock.schedule_interval(lambda dt: server.run(), 1 / 30)
    SessionManagementApp().run()