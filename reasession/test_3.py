import reapy as rpr
from reapy import reascript_api as RPR
from simple_test_data import data as test_data
import typing as ty
SECTION = 'REASESSION'

message = [0xb0, 0x40, 0x50]
# print(bytes(message))
# --- b'\x90@P'

chars = ''.join([chr(x) for x in message])
# print(chars)
# --- @P

cm_id = rpr.get_command_id('_RS5363a1728d2e87be1a7d472621c512ebf404b8da')

# print(chars.encode())  # utf-8
# # --- b'\xc2\x90@P'

# print(chars.encode('latin-1'))
# # --- b'\x90@P'
pr = rpr.Project()
tr = pr.tracks[2]
item = tr.items[0]
take = item.active_take


def perform_insert(data: str) -> None:

    # rpr.set_ext_state(SECTION, 'build_midi_on_track_project', pr.id)
    _, _, _, guid, _ = RPR.GetSetMediaItemTakeInfo_String(
        take.id, 'GUID', 'stringNeedBig', False)
    rpr.set_ext_state(SECTION, 'build_midi_on_track_take', str(guid))
    # rpr.set_ext_state(SECTION, 'build_midi_on_track_buf', chars)
    # rpr.set_ext_state(SECTION, 'build_midi_on_track_ppq', str(ppq))
    rpr.set_ext_state(SECTION, 'build_midi_on_track_evts', data)
    rpr.perform_action(cm_id)


# with rpr.inside_reaper():
#     with rpr.undo_block('insert multiple sysex'):
#         for i in range(20, 21):
#             perform_insert(i/10)
# perform_insert(3)

def get_buf(evt: ty.Dict[str, object]) -> str:
    out = ''
    prefix = [0xFF, 0x52, 0x50, 0x62]
    bus = evt['bus']
    buf = evt['buf']
    for idx, val in enumerate((*prefix, bus, *buf)):
        out += f'[{idx+1}]={int(val)},'
    # out = 
    return out[:-1]


def pack_data(data: ty.List[ty.Dict[str, object]], take: rpr.Take) -> str:
    out = '{'
    for idx, evt in enumerate(data):
        ppq = take._resolve_midi_unit((evt['qn'],), 'beats')[0]
        out += f'[{idx+1}]={{["ppq"]={ppq},["buf"]={{{get_buf(evt)}}}}},'
    out = out[:-1]+'}'
    # print(out)
    return out

with rpr.inside_reaper():
    perform_insert(pack_data(test_data, take))
