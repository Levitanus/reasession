import reapy as rpr
import reapy.reascript_api as RPR
from networking import SlaveTCPHandler
from networking import DEF_HOST
from networking import DEF_PORT
import socketserver as ss
from basic_handlers import PrintHandler
from basic_handlers import PingHandler

HOST, PORT = DEF_HOST, DEF_PORT

SlaveTCPHandler.register(PrintHandler())
SlaveTCPHandler.register(PingHandler())

server = ss.ThreadingTCPServer(
    (HOST, PORT), SlaveTCPHandler, bind_and_activate=False
)
server.timeout = .01
server.allow_reuse_address = True
server.server_bind()
server.server_activate()


def main_loop() -> None:
    # rpr.print('run')
    server.handle_request()
    if rpr.is_inside_reaper():
        rpr.defer(main_loop)
    else:
        main_loop()


def at_exit() -> None:
    rpr.print('closing server')
    server.server_close()


rpr.at_exit(at_exit)
main_loop()
