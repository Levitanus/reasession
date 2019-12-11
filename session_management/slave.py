import reapy as rpr
import reapy.reascript_api as RPR
from networking import ReaperServer
from networking import DEF_HOST
from networking import DEF_PORT
import socketserver as ss
from threading import Thread
from threading import enumerate as tr_enum
from threading import main_thread
from basic_handlers import PrintHandler
from basic_handlers import PingHandler
from common import log
import typing as ty

log.enable_print()
log.enable_console()

HOST, PORT = DEF_HOST, DEF_PORT

handlers = [PrintHandler, PingHandler]
server = ReaperServer(HOST, PORT, handlers)


def main_loop() -> None:
    server.run()
    if rpr.is_inside_reaper():
        rpr.defer(main_loop)
    else:
        main_loop()


def at_exit() -> None:
    server.at_exit()


print('starting slave')
rpr.at_exit(at_exit)
main_loop()
