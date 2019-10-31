from reaper_python import *
from networking import DEF_HOST, DEF_PORT
from TCP_funcs import rpr_print
retval = RPR_SetExtState('TCP_PACKAGE', 'DATA', 'test string data', True)
retval = RPR_SetExtState('TCP_PACKAGE', 'HOST', DEF_HOST, True)
retval = RPR_SetExtState('TCP_PACKAGE', 'PORT', str(DEF_PORT), True)

rpr_print(f'added ExtState "TCP_PACKAGE"')
rpr_print('TCP_PACKAGE: DATA = test string data')
rpr_print(f'TCP_PACKAGE: HOST = {DEF_HOST}')
rpr_print(f'TCP_PACKAGE: PORT = {DEF_PORT}')
