import jack
import warnings
import reapy as rpr
import pytest as ptst
from ..connections import backend as bck


class MonkeyJackPort:
    def __init__(self, name: str, uuid: str = 'basic_uuid') -> None:
        self.name = name
        self.uuid = uuid


class MonkeyJackPortDump(bck.JackPortDump):
    def __init__(self, port, connection):
        self.port = port
        self.connection = connection


def test_parce_port_name(monkeypatch):
    class Port:
        def __init__(self, name: str) -> None:
            self.name = name

    port = Port('REAPER:MIDI Output 3')
    assert bck.parce_port_name(port) == ('REAPER', 'MIDI Output 3')
    port.name = 'my_strange port name:'
    with ptst.raises(bck.PortNameError, match='strange port name'):
        bck.parce_port_name(port)


def test_SlaveJackPort(monkeypatch):
    monkeypatch.setattr(jack, 'MidiPort', MonkeyJackPort)
    connections = [
        jack.MidiPort('192.168.2.2:port1'),
        jack.MidiPort('somehost:port1'),
    ]
    port1 = bck.SlaveJackPort(
        port=jack.MidiPort('test_port'), connections=connections
    )
    print(port1)
    assert repr(port1) == 'test_port -> 192.168.2.2:port1'
    connections.append(jack.MidiPort('192.168.2.2:port2'))
    with ptst.raises(bck.JackPortError, match='too many connections'):
        bck.SlaveJackPort(
            port=jack.MidiPort('test_port'), connections=connections
        )


def test_SystemJackPort(monkeypatch):
    monkeypatch.setattr(jack, 'MidiPort', MonkeyJackPort)
    connections = [
        jack.MidiPort('system:port1'),
        jack.MidiPort('somehost:port1'),
    ]
    port1 = bck.SystemJackPort(
        port=jack.MidiPort('test_port'), connections=connections
    )
    # print(port1)
    assert repr(port1) == 'system:port1 -> test_port'
    connections.append(jack.MidiPort('system:port2'))
    with ptst.raises(bck.JackPortError, match='too many connections'):
        bck.SystemJackPort(
            port=jack.MidiPort('test_port'), connections=connections
        )


def test_JackPortDump(monkeypatch):
    monkeypatch.setattr(jack, 'MidiPort', MonkeyJackPort)
    port1 = bck.SlaveJackPort(
        port=jack.MidiPort('test_host:test_port', uuid='uuid1'),
        connections=[jack.MidiPort('192.168.2.2:test_port', uuid='uuid2')]
    )
    dmp = bck.JackPortDump(port1)
    assert dmp.port == {
        'host': 'test_host',
        'name': 'test_port',
        'uuid': 'uuid1'
    }
    assert dmp.connection == {
        'host': '192.168.2.2',
        'name': 'test_port',
        'uuid': 'uuid2'
    }


# --------------------TOP-----------


class TestException(Exception):
    def __init__(self, obj: object) -> None:
        super().__init__("test exception: see it's object for details")


# def test_Connector(monkeypatch):

#     monkeypatch.setattr(bck, 'JackPortDump', MonkeyJackPortDump)
#     monkeypatch.setattr(jack, 'MidiPort', MonkeyJackPort)
#     host = '192.168.2.2'
#     name = 'MIDI input'
#     slave_ports = []
#     master_ports = []
#     for i in range(3):
#         slave_ports.append(
#             bck.JackPortDump(
#                 port={
#                     'host': host,
#                     'name': f'{name} {i}',
#                     'uuid': f'uuid{i}'
#                 },
#                 connection={
#                     'host': 'system',
#                     'name': f'MIDI capture{i}',
#                     'uuid': f'uuid_s{i}'
#                 }
#             )
#         )
#         master_ports.append(
#             bck.SlaveJackPort(
#                 jack.MidiPort(name='REAPER:MIDI output {i}', uuid='rout{i}'), [
#                     jack.MidiPort(
#                         name='192.168.2.2:midi_to_slave_{i}', uuid='sin{i}'
#                     )
#                 ]
#             )
#         )
#     master_ports.append(
#         bck.SlaveJackPort(
#             jack.MidiPort(name='REAPER:MIDI output {4}', uuid='rout{4}'), []
#         )
#     )
#     cnctr = bck.Connector(master_ports, slave_ports)
#     with ptst.raises(TestException) as e:
#         cnctr.connect_to_slave(
#             master_project, master_track, slave_ip, slave_project, slave_track
#         )
#         assert e.obj == {''}
