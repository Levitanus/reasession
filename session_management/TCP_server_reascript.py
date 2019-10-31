from networking import SlaveTCPHandler
import socketserver as ss
from networking import IHandler

from TCP_funcs import rpr_print
from TCP_funcs import get_host_port
from reaper_python import *

HOST, PORT = get_host_port()


class ExtStateHandler(IHandler):
    extname = 'TCP_PACKAGE'
    extkey = 'DATA'

    def can_handle(self, data_type: bytes) -> bool:
        if data_type == b'ext_set':
            rpr_print('can handle ext_set')
            return True
        if data_type == b'ext_get':
            rpr_print('can handle ext_get')
            return True
        rpr_print(f"can't handle {data_type}")
        return False

    def handle(self, data_type: bytes, data: bytes) -> bytes:
        # rpr.print(str(data, 'utf-8'))
        if data_type == b'ext_get':
            return self._get_state(data)
        return self._set_state(data)

    def _get_state(self, data: bytes) -> bytes:
        retval = RPR_GetExtState(self.extname, self.extkey)
        return bytes(str(retval), 'utf-8')

    def _set_state(self, data: bytes) -> bytes:
        retval = RPR_SetExtState(
            self.extname, self.extkey, str(data, 'utf-8'), False
        )
        return bytes(str(retval), 'utf-8')


SlaveTCPHandler.register(ExtStateHandler())

server = ss.ThreadingTCPServer(
    (HOST, PORT), SlaveTCPHandler, bind_and_activate=False
)
server.timeout = .01
server.allow_reuse_address = True
server.server_bind()
server.server_activate()
rpr_print(f'serving on {server.server_address}')


def main_loop() -> None:
    # rpr.print('run')
    server.handle_request()
    RPR_defer('main_loop()')


def at_exit() -> None:
    rpr_print('closing server')
    server.server_close()


RPR_atexit('at_exit()')
main_loop()
