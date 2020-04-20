import reapy as rpr
from reapy import reascript_api as RPR
from enum import Enum

take = rpr.Project().selected_items[0].active_take

RPR.MIDI_SetCC(take.id, 1, selected=None, muted=None, ppqpos=None,
                   chan_msg=None, channel=None, msg2=None, msg3=None, sort=None)
