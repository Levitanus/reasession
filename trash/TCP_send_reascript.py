'''
Application example using build() + return
==========================================

An application can be built if you return a widget on build(), or if you set
self.root.
'''
from networking import send_data
from TCP_funcs import rpr_print
from TCP_funcs import get_host_port
import socket as st
from reaper_python import *
# data, host, port = "test string data", '127.0.0.1', 49541
host, port = get_host_port()
data = RPR_GetExtState('TCP_PACKAGE', 'DATA')
try:
    retval = send_data("ext_set", data, host, port)
except st.timeout as e:
    retval = f'connection timeout:\n{e}'
except ConnectionRefusedError as e:
    retval = f'connection refused:\n{e}'

rpr_print(f'sent "{data}" to {host}: {port}', f'returned: {retval}', sep='\n')
# print(f'sent "{data}" to {host}: {port}', f'returned: {retval}', sep='\n')
