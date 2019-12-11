import socket as st
import socketserver as ss
import json as js
import typing as ty
from threading import Thread
import reapy as rpr
from common import log
# import typing_extensions as te
# from reaper_python import *

DEF_HOST: str = '127.0.0.1'
DEF_PORT: int = 49541


def _fill_prefix(prefix: str) -> bytes:
    """Fills head of given string by zeros to make it of length 10"""
    return str(prefix).encode().zfill(10)


def _encode_data(data: object) -> bytes:
    if isinstance(data, bytes):
        data_enc = data
    elif isinstance(data, str):
        data_enc = bytes(data, 'utf-8')
    else:
        data_enc = bytes(js.dumps(data), 'utf-8')
    return data_enc


def send_data(
    type_: str, data: object, host: str = DEF_HOST, port: int = DEF_PORT
) -> str:
    """Send any data to destination slave.

    type: str
        string up to 10 bytes, which will be handled
        by one of IHandler classes
    data: object
        any JSONable object, if it is str or bytes
        will be sent as bytes encoded as utf-8
    host: str
        ip address of slave server
    port: int
        port of slave server
    """
    with st.socket(st.AF_INET, st.SOCK_STREAM) as sock:
        # Connect to server and send data
        type_enc = _fill_prefix(type_)
        data_enc = _encode_data(data)
        size = _fill_prefix(str(len(data_enc)))
        sock.settimeout(0.1)

        sock.connect((host, port))
        sock.sendall(type_enc + size + data_enc)

        # Receive data from the server and shut down
        received = str(sock.recv(1024), "utf-8")
    return received


class IHandler:
    """Base class for slave handlers.

    can_handle(self, data_type: bytes) -> bool:
        should return True if class can handle data of type
    handle(self, data_type: bytes, data: bytes) -> bytes:
        should return bytes to response back to master
        if no response expected use 'success' or 'fail'
    """
    def can_handle(self, data_type: bytes) -> bool:
        """Return True if class can handle data of type."""
        return False

    def handle(self, data_type: bytes, data: bytes) -> bytes:
        """Process data and return bytes-like response."""
        return bytes('%s passed' % self.__class__.__name__, 'utf-8')


class SlaveTCPHandler(ss.BaseRequestHandler):
    """TCP Handler to be used by socketserver.

    Any instancce of IHandler can be registered to handler and process
    incoming packages.
    """
    request: st.socket
    client_address: ty.Tuple[str, int]
    _handlers: ty.List[IHandler] = []

    @classmethod
    def register(cls, handler: IHandler) -> None:
        """Register handler to be proceed by server."""
        cls._handlers.append(handler)

    def handle(self) -> None:
        """Get data from client and process with handlers."""
        # RPR_ShowConsoleMsg('handle' + '\n')
        package = self.request.recv(1024)
        data_type = package[:10].strip(b'0')
        data_size = package[11:20].strip(b'0')
        data = package[20:]
        data = self._request_data(data, data_size, package)
        response = self._get_response(data_type, data)
        try:
            self.request.sendall(response)
        except IOError as e:
            log(e)

    def _get_response(self, data_type: bytes, data: bytes) -> bytes:
        response = b''
        for nr, handler in enumerate(self._handlers):
            if handler.can_handle(data_type):
                if nr > 0:
                    response += b'\n'
                response += handler.handle(data_type, data)
        return response

    def _request_data(
        self, data: bytes, data_size: bytes, package: bytes
    ) -> bytes:
        while len(data) < int(data_size):
            package = self.request.recv(1024)
            if not package:
                break
            data = data + package
        return data


class ServerThread(Thread):
    """Thread, supposing to run socketserver.

    Example:
        handlers = [PrintHandler, PingHandler]
        s_server = ReaperServer(handlers, main, host_port=(HOST, PORT))
        rpr.at_exit(s_server.stop)
        s_server.start()
    """
    def __init__(self, server: ss.ThreadingTCPServer) -> None:
        super().__init__(daemon=True)
        self.server = server

    def run(self) -> None:
        """Start server daemon."""
        self.server.serve_forever()


class ReaperServer:
    at_exit: ty.Optional[ty.Callable[[], None]]

    def __init__(
        self,
        handlers: ty.List[ty.Type[IHandler]],
        event_loop: ty.Callable[[], None],
        host_port: ty.Tuple[str, int] = (DEF_HOST, DEF_PORT),
        at_exit: ty.Optional[ty.Callable[[], None]] = None
    ) -> None:
        log('initializing server:')
        self.host, self.port = host_port
        self.handler = SlaveTCPHandler
        for handler in handlers:
            self.handler.register(handler())
        self.event_loop = event_loop
        self.at_exit = at_exit
        rpr.at_exit(self.stop)
        log('creating a TCP server')
        self.server = ss.ThreadingTCPServer(
            (self.host, self.port),
            SlaveTCPHandler,
            bind_and_activate=False,
        )
        self.server.allow_reuse_address = True

        log('creating a TCP server thread')
        self.server_thread = ServerThread(self.server)

    def start(self) -> None:
        """Start TCP server and run event loop."""
        log('starting TCP server')
        self.server.server_bind()
        self.server.server_activate()
        self.server_thread.start()
        log('running event loop')
        self._run()

    def stop(self) -> None:
        """Stop server and cleanup."""
        log('closing everything')
        self._cleanup()
        log('done')

    def _run(self) -> None:
        self.event_loop()
        rpr.defer(self._run)

    def _cleanup(self) -> None:
        if self.at_exit is not None:
            log('perform at_exit')
            self.at_exit()
        self.server.shutdown()
        self.server.server_close()
        self.server_thread.join()


if __name__ == '__main__':
    test_data = 'test package'
    test_received = send_data('print', test_data)
    print("Sent:     {}".format(test_data))
    print("Received: {}".format(test_received))
