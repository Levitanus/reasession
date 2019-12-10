from typing import Tuple
from reaper_python import *
from networking import DEF_HOST
from networking import DEF_PORT


def rpr_print(*msg, sep=' ') -> None:
    nmsg = str(msg)
    if isinstance(msg, Tuple):
        nmsg = str(msg[0])
        for i in msg[1:]:
            nmsg += sep + str(i)
    RPR_ShowConsoleMsg(nmsg + '\n')


def get_host_port() -> Tuple[str, int]:
    if not RPR_HasExtState('TCP_PACKAGE', 'HOST'):
        rpr_print('ext state "TCP_PACKAGE, HOST" does not exists')
        return DEF_HOST, DEF_PORT
    if not RPR_HasExtState('TCP_PACKAGE', 'PORT'):
        rpr_print('ext state "TCP_PACKAGE, PORT" does not exists')
        return DEF_HOST, DEF_PORT
    host = RPR_GetExtState('TCP_PACKAGE', 'HOST')
    port = int(RPR_GetExtState('TCP_PACKAGE', 'PORT'))
    rpr_print(host, port, type(host), type(port))
    return host, port