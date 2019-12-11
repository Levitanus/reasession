# import reapy.reascript_api as RPR
import reapy as rpr
from networking import ReaperServer
from networking import DEF_HOST
from networking import DEF_PORT
from basic_handlers import PrintHandler
from basic_handlers import PingHandler
from common import Log

Log.active = True

HOST, PORT = DEF_HOST, DEF_PORT


def main() -> None:
    pass


handlers = [PrintHandler, PingHandler]
s_server = ReaperServer(handlers, main, host_port=(HOST, PORT))
# rpr.at_exit(s_server.stop)
rpr.defer(s_server.start)
