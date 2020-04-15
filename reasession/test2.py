import reapy as rpr
from reapy import reascript_api as RPR

s_pos, e_pos = 1, 12.0

pr = rpr.Project()
tr = pr.selected_tracks[0]
item = tr.add_midi_item(start=s_pos, end=e_pos, quantize=True)
rpr.print(item)
take = item.active_take
rpr.print(take)
body = [
    # 0xf0,
    # 0xFF,
    # 0x52,
    # 0x50,
    # 0x62,

    # 0x02,

    0x90,
    64,
    85,
    # 2,
    # 0xf7
]
# take.add_sysex(s_pos+2, body)
rpr.print(0xf7)
rpr.print(body)
# body_b = bytes(body)
body_b = '\\'.join([hex(i) for i in body])
rpr.print(body_b)
# body_b = bytes.fromhex(body_b)
# rpr.print(body_b)
body_b = ''.join([chr(i) for i in body])
rpr.print(body_b.encode('latin1'))
size = len(body_b)
rpr.print(size)
ppqpos = take._resolve_midi_unit((2,), unit='beats')[0]
result = RPR.MIDI_InsertTextSysexEvt(take.id, False, False,
                                     ppqpos, -1, body_b.encode()[1:], size)
# result = RPR.MIDI_InsertEvt(take.id, False, False, ppqpos, body_b, size)
rpr.print(result)
rpr.print(0xC2)
RPR.MIDI_Sort(take.id)

# item = tr.items[0]
# take = item.active_take
# print(take)

# retval, _, _, _, _, _, msg, msg_sz = RPR.MIDI_GetEvt(
#     take.id, 0, 1, 1, 1, 'looongmessage', 65000)
# rpr.print(retval, msg, msg_sz)
