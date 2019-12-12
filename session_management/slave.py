# import reapy.reascript_api as RPR
import typing as ty
import socket as st
from time import sleep

import reapy as rpr
import reapy.reascript_api as RPR

from networking import ReaperServer
from networking import DEF_HOST
from networking import DEF_PORT
from networking import Announce
from threading import Thread
from basic_handlers import PrintHandler
from basic_handlers import PingHandler
from common import log
import set_slave_ip

from config import EXT_SECTION, ADDRESS_KEY_SLAVE

from socket import (socket, AF_INET, SOCK_DGRAM, SOL_SOCKET, SO_BROADCAST)

# log.enable_print()
# log.enable_console()
HOST: str
PORT: int
HOST, PORT = DEF_HOST, DEF_PORT

if not rpr.has_ext_state(EXT_SECTION, ADDRESS_KEY_SLAVE):
    host = set_slave_ip.cnoose_ip()
    if host is None:
        rpr.show_message_box(text='cannot run slave', title='error', type="ok")
        raise RuntimeError('cannot run slave')
    HOST = host
else:
    HOST = rpr.get_ext_state(EXT_SECTION, ADDRESS_KEY_SLAVE)

handlers = [PrintHandler, PingHandler]
server = ReaperServer(HOST, PORT, handlers)

announce = Announce(HOST, PORT)


def main_loop() -> None:
    server.run()
    announce.run()
    if rpr.is_inside_reaper():
        rpr.defer(main_loop)
    else:
        sleep(.03)
        main_loop()


def at_exit() -> None:
    server.at_exit()


log(f'starting slave on {HOST}:{PORT}')
if rpr.is_inside_reaper():
    rpr.at_exit(at_exit)
main_loop()
