'''
Application example using build() + return
==========================================

An application can be built if you return a widget on build(), or if you set
self.root.
'''
from reaper_python import *
from networking import send_data
from TCP_funcs import rpr_print
from TCP_funcs import get_host_port
import socket as st

host, port = get_host_port()
data = 'NO_DATA'
try:
    data = send_data('ext_state_get', "getting(doesn't matters)", host, port)
except st.timeout as e:
    data = f'connection timeout:\n{e}'
except ConnectionRefusedError as e:
    data = f'connection refused:\n{e}'
RPR_SetExtState('TCP_PACKAGE', 'DATA', data, False)
rpr_print(f'get from {host}: {port}', f'returned: {data}', sep='\n')
