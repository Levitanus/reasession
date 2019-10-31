from reaper_python import *
from networking import DEF_HOST, DEF_PORT
retval = RPR_SetExtState('TCP_PACKAGE', 'DATA', 'test string data', True)
retval = RPR_SetExtState('TCP_PACKAGE', 'HOST', DEF_HOST, True)
retval = RPR_SetExtState('TCP_PACKAGE', 'PORT', str(DEF_PORT), True)