from reaper_python import *
retval = RPR_GetExtState('TCP_PACKAGE', 'DATA')
RPR_ShowConsoleMsg(retval)