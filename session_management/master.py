from threading import Thread
from time import sleep
import socket as sock

import reapy as rpr
import reapy.reascript_api as RPR

from networking import ReaperServer
from networking import IHandler
from networking import send_data
from networking import DEF_HOST
from common import log, Log
from basic_handlers import PingHandler

Log.active = True

SLAVE_PORT: int = 49541
SERVER_PORT: int = 49542
GUI_PORT: int = 49543


class SlavePing(Thread):
    active: bool

    def __init__(self) -> None:
        super().__init__(daemon=True)
        self.active = True

    def run(self) -> None:
        while self.active:
            try:
                response = send_data('ping', 'ping', port=SLAVE_PORT)
                log('slave:', response)
            except ConnectionError:
                log('slave is dead')
            except sock.timeout:
                log('slave is dead')
            except ConnectionRefusedError as e:
                log(str(e))
            sleep(1)


ping_thread = SlavePing()
ping_thread.start()

# def main() -> None:
#     rpr.defer(main)


def cleanup() -> None:
    global ping_thread
    ping_thread.active = False
    if ping_thread.is_alive():
        ping_thread.join()


def loop() -> None:
    pass


log('run main at master')
server = ReaperServer(
    [PingHandler], loop, at_exit=cleanup, host_port=(DEF_HOST, SERVER_PORT)
)
rpr.defer(server.start)

# if __name__ != '__main__':
# rpr.at_exit(cleanup)
# rpr.defer(main)
