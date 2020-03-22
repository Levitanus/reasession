import socket as st
import socketserver as ss
# import json as js
import pickle as pcl
import typing as ty
from threading import current_thread
from threading import Thread
from threading import main_thread
from threading import enumerate as tr_enum
from reasession.common import log
from reasession.common import TimeCallback
from reasession.config import ANNOUNCE_STRING

DEF_HOST: str = '127.0.0.1'
DEF_PORT: int = 49541
MASTER_PORT: int = 49542
GUI_PORT: int = 49543


def _fill_prefix(prefix: str) -> bytes:
    """Fills head of given string by zeros to make it of length 10"""
    assert len(prefix) <= 10, 'too long prefix'
    assert prefix, 'no point of making prefix with null string'
    return str(prefix).encode().zfill(10)


def encode_data(data: object) -> bytes:
    if isinstance(data, bytes):
        data_enc = data
    elif isinstance(data, str):
        data_enc = bytes(data, 'utf-8')
    else:
        # data_enc = bytes(js.dumps(data), 'utf-8')
        data_enc = pcl.dumps(data)
    return data_enc


def send_data(
    type_: str,
    data: object,
    host: str = DEF_HOST,
    port: int = DEF_PORT,
    timeout: float = 0.1
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
        data_enc = encode_data(data)
        size = _fill_prefix(str(len(data_enc)))
        sock.settimeout(timeout)

        sock.connect((host, port))
        sock.sendall(type_enc + size + data_enc)

        # Receive data from the server and shut down
        received = str(sock.recv(1024), "utf-8")
        # sock.close()
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
        assert isinstance(
            handler, IHandler
        ), 'accept only instances of IHandler'
        cls._handlers.append(handler)

    def handle(self) -> None:
        """Get data from client and process with handlers."""
        # self.request = st.socket()
        # conn = self.request.accept()
        package = self.request.recv(1024)
        data_type = package[:10].strip(b'0')
        data_size = package[11:20].strip(b'0')
        data = package[20:]
        data = self._request_data(data, data_size, package)
        response = self._get_response(data_type, data)
        log('response length:', len(response))
        log(f'tread: {current_thread()}')
        self.request.sendall(response)
        self.request.close()
        # log(self.request._closed)

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


class ReaperServer:
    """TCP server able to run in reascript defer.

    Example:
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
        if rpr.is_inside_reaper():
            rpr.at_exit(at_exit)
        main_loop()
    """
    def __init__(
        self, host: str, port: int, handlers: ty.List[ty.Type[IHandler]]
    ) -> None:
        for handler in handlers:
            SlaveTCPHandler.register(handler())
        self._server = ss.TCPServer(
            (host, port), SlaveTCPHandler, bind_and_activate=False
        )
        self._server.timeout = .02
        self._server.allow_reuse_address = True
        log(f'starting server at {host}:{port}')
        self._server.server_bind()
        self._server.server_activate()

    def register_handler(self, handler: IHandler) -> None:
        SlaveTCPHandler.register(handler)

    def run(self) -> None:
        """Callback to be put in defer loop."""
        Thread(target=self._server.handle_request).start()

    def at_exit(self) -> None:
        """Has to be put into repy.at_exit."""
        log('closing master')
        log('active threads:')
        for tr in tr_enum():
            if tr is main_thread():
                continue
            log(f'    {tr}')
        for tr in tr_enum():
            if tr is main_thread():
                continue
            log(f'joining {tr} thread')
            tr.join(.1)
            if tr.is_alive():
                log('timeout')
        log('closing server')
        self._server.server_close()
        log('master closed')


class Announce:
    """Broadcast ip address once per 5 seconds."""
    def __init__(self, host: str, port: int) -> None:
        self._s = st.socket(st.AF_INET, st.SOCK_DGRAM)  # create UDP socket
        self._s.bind(('', 0))
        # this is a broadcast socket
        self._s.setsockopt(st.SOL_SOCKET, st.SO_BROADCAST, 1)
        self._timer = TimeCallback(self._cb, 5)
        self._data = ANNOUNCE_STRING
        self._host = host
        self._port = port

    def _cb(self) -> None:
        self._s.sendto(
            self._data + bytes(self._host, 'utf-8'),
            ('<broadcast>', self._port)
        )
        log("sent service announcement")

    def run(self) -> None:
        """Has to be put into defer loop."""
        self._timer.run()


class Discovery:
    """Handle requests from slaves and get their IP."""
    def __init__(
        self, port: int, on_discovery: ty.Callable[[str], None]
    ) -> None:
        self._s = st.socket(st.AF_INET, st.SOCK_DGRAM)
        self._s.bind(('', port))
        self._s.setsockopt(st.SOL_SOCKET, st.SO_REUSEADDR, 1)
        self._s.settimeout(4)
        self._timer = TimeCallback(self._cb, 5)
        self._on_discovery = on_discovery
        self._exited = False

    def run(self) -> None:
        """Callback to be put in defer loop."""
        self._timer.run()

    def _cb(self) -> None:
        Thread(target=self._listen).start()

    def _listen(self) -> None:
        if self._exited:
            return
        try:
            data, addr = self._s.recvfrom(1024)  # wait for a packet
            log.enable_console()
            if data.startswith(ANNOUNCE_STRING):
                log(
                    "got service announcement from",
                    data[len(ANNOUNCE_STRING):]
                )
                # log(addr)
                self._on_discovery(str(data[len(ANNOUNCE_STRING):], 'utf-8'))
        except st.timeout:
            return

    def at_exit(self) -> None:
        """Callback to be put into the at_exit call."""
        log('closing discovery')
        log('active threads:')
        self._exited = True
        for tr in tr_enum():
            if tr is main_thread():
                continue
            log(f'    {tr}')
        for tr in tr_enum():
            if tr is main_thread():
                continue
            log(f'joining {tr} thread')
            tr.join(.1)
            if tr.is_alive():
                log('timeout')
        log('closing socket')
        self._s.close()
        log('discovery closed')


if __name__ == '__main__':
    log.enable_print()
    test_data = 'test package'
    test_received = send_data('ping', 'ping', port=49542)
    log("Sent:     {}".format(test_data))
    log("Received: {}".format(test_received))
