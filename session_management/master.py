import typing as ty

import reapy as rpr
import reapy.reascript_api as RPR

from networking import ReaperServer
from networking import DEF_HOST, MASTER_PORT, DEF_PORT
from networking import send_data
from basic_handlers import PrintHandler
from basic_handlers import PingHandler
from common import log
from common import TimeCallback

from networking import Discovery

log.enable_print()
# log.enable_console()


def ping() -> None:
    test_received = ''
    try:
        test_received = send_data('ping', 'ping')
    except ConnectionRefusedError as e:
        log(f'slave is dead: {e}')
        return
    if test_received:
        log(f'slave: {test_received.strip()}')


pinger = TimeCallback(ping, time=1)


def on_discovery() -> None:
    pass


disc = Discovery(DEF_PORT, on_discovery)

HOST, PORT = DEF_HOST, MASTER_PORT

handlers = [PrintHandler, PingHandler]
gui_server = ReaperServer(HOST, PORT, handlers)


def main_loop() -> None:
    pinger.run()
    gui_server.run()
    disc.run()
    if rpr.is_inside_reaper():
        rpr.defer(main_loop)
    else:
        main_loop()


def at_exit() -> None:
    gui_server.at_exit()
    disc.at_exit()


log('starting master')
rpr.at_exit(at_exit)
main_loop()
