import typing as ty

import reapy as rpr
import reapy.reascript_api as RPR

from networking import ReaperServer
from networking import DEF_HOST, MASTER_PORT, DEF_PORT
from basic_handlers import PrintHandler
from basic_handlers import PingHandler
from common import log
from common import is_stopped

from slaves import Slaves

log.enable_print()
log.enable_console()

slaves = Slaves(DEF_PORT)

HOST, PORT = DEF_HOST, MASTER_PORT

handlers = [PrintHandler, PingHandler]
gui_server = ReaperServer(HOST, PORT, handlers)


def main_loop() -> None:
    if is_stopped():
        slaves.run()
        gui_server.run()
    rpr.defer(main_loop)


def at_exit() -> None:
    gui_server.at_exit()
    slaves.at_exit()


log('starting master')
rpr.at_exit(at_exit)
main_loop()
