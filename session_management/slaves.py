import typing as ty
from networking import Discovery
from networking import send_data
from networking import GUI_PORT
from common import TimeCallback
from common import log
import socket as st
import reapy as rpr
from threading import Thread


class SlaveForMaster:
    def __init__(self, host: str, port: int) -> None:
        self._host = host
        self._port = port


class Slaves:
    def __init__(self, slaves_port: int) -> None:
        self._slaves_port = slaves_port
        self._slaves_active: ty.Dict[str, SlaveForMaster] = {}
        self._discovery = Discovery(slaves_port, self._on_discovery)
        self._pinger = TimeCallback(self._ping, time=1)

    def _send_slaves_to_gui(self) -> None:
        send_data(
            'slave_list', [key for key in self._slaves_active],
            port=GUI_PORT,
            timeout=0.03
        )

    def _on_discovery(self, host: str) -> None:
        # pass
        # log('on discovery')
        if host not in self._slaves_active:
            log(f'slave on {host} registered')
            self._slaves_active[host] = SlaveForMaster(host, self._slaves_port)
            rpr.defer(self._send_slaves_to_gui)

    def _ping(self) -> None:
        # log('ping')
        response = ''
        active = self._slaves_active.copy()
        for host in active:
            try:
                response = send_data(
                    'ping', 'ping', host, self._slaves_port, timeout=0.03
                )
            except ConnectionRefusedError as e:
                log(f'slave {host} is dead: {e}')
                del self._slaves_active[host]
                return
            except st.timeout as e:
                log(f'timeout on host: {host}')
                rpr.show_message_box(
                    'slave server on this machine started before master.\n' +
                    'please, restart both scripts in the proper order.',
                    'connection timeout'
                )
                raise e
            if response:
                log(f'slave {host} is alive')

    def run(self) -> None:
        self._pinger.run()
        self._discovery.run()

    def at_exit(self) -> None:
        self._discovery.at_exit()

    def active_slaves(self) -> ty.Dict[str, SlaveForMaster]:
        return self._slaves_active
