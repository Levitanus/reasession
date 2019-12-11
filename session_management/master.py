import reapy as rpr
import reapy.reascript_api as RPR
from networking import SlaveTCPHandler
from networking import ReaperServer
from networking import DEF_HOST
from networking import DEF_PORT
import socketserver as ss
import socket as st
from threading import Thread
from threading import enumerate as tr_enum
from threading import main_thread
from basic_handlers import PrintHandler
from basic_handlers import PingHandler
import typing as ty
from networking import send_data
from time import sleep
from common import log

log.enable_print()
# log.enable_console()

# HOST, PORT = DEF_HOST, DEF_PORT


class Pinger:
    def __init__(self) -> None:
        self._counter = 0

    def run(self) -> None:
        if self._counter >= 30:
            self._ping()
            self._counter = 0
        self._counter += 1

    def _ping(self) -> None:
        test_received = ''
        try:
            test_received = send_data('ping', 'ping')
        except ConnectionRefusedError as e:
            log(f'slave is dead: {e}')
            return
        if test_received:
            log(f'slave: {test_received.strip()}')


pinger = Pinger()

HOST, PORT = DEF_HOST, 49542

handlers = [PrintHandler, PingHandler]
gui_server = ReaperServer(HOST, PORT, handlers)


def main_loop() -> None:
    pinger.run()
    gui_server.run()
    if rpr.is_inside_reaper():
        rpr.defer(main_loop)
    else:
        main_loop()


def at_exit() -> None:
    gui_server.at_exit()


print('starting master')
rpr.at_exit(at_exit)
main_loop()
