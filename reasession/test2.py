import reapy as rpr
from reapy import reascript_api as RPR
import typing as ty
import typing_extensions as te
from enum import IntFlag
import struct


class CCShape(IntFlag):
    no_shape = 0
    linear = 16
    slow_start_end = 32
    fast_start = 16 | 32
    fast_end = 64
    beizer = 16 | 64


Message = te.TypedDict(
    'Message', {
        'ppq': int,
        'selected': bool,
        'muted': bool,
        'cc_shape': CCShape,
        'buf': ty.List[int],
    }
)

# for i in [1, 2, 16, 32, 16 | 32, 64, 16 | 64, 1 | 16, 1 | 32]:
#     print(CCShape(i & 0b11110000))

# exit()

take = rpr.Project().selected_items[0].active_take
retval, take, bufNeedBig, bufNeedBig_sz = RPR.MIDI_GetAllEvts(
    take.id, '', 1024
)

# print(bufNeedBig_sz, bufNeedBig.encode('latin-1'), sep=': ')


def unpack_events(msg_str: str) -> ty.List[Message]:
    msg = msg_str.encode('latin-1')
    out: ty.List[Message] = []
    i = 0
    ppq = 0
    while i < len(msg):
        ofst, flag, len_ = (
            struct.unpack('<I', msg[i:i + 4])[0], int(msg[i + 4]),
            struct.unpack('<I', msg[i + 5:i + 9])[0]
        )
        ppq += ofst
        buf_b = msg[i + 9:i + 9 + len_]
        buf = [int(b) for b in buf_b]
        i += 9 + len_
        if len_ == 0:
            break
        out.append(
            Message(
                ppq=ppq,
                selected=bool(flag & 1),
                muted=bool(flag & 2),
                cc_shape=CCShape(flag & 0b11110000),
                buf=buf
            )
        )
    return out


def pack_events(events: ty.List[Message], take: rpr.Take) -> str:
    out = b''
    last_ppq = 0
    for msg in events:
        evt = b''
        ofst_i = msg['ppq'] - last_ppq
        print(ofst_i)
        if ofst_i > 4294967295:
            raise NotImplementedError(
                'ofset larger than 4294967295 currently not supported'
            )
            # something done with big offset
            # it is about many-many-many hours between events
            # (1 hour is about 8000000 ppq in 120 bpm)
        ofst = struct.pack('<I', ofst_i)
        evt += ofst
        last_ppq = msg['ppq']

        flag = bytes(
            [
                int(msg['selected']) | (int(msg['muted']) << 1)
                | msg['cc_shape']
            ]
        )
        evt += flag

        len_ = struct.pack('<I', len(msg['buf']))
        evt += len_

        buf = bytes(msg['buf'])
        evt += buf
        out += evt
    return out.decode('latin-1')


unpacked = unpack_events(bufNeedBig)
# print(*unpacked, sep='\n-------\n')

packed = pack_events(unpacked, rpr.Project().selected_items[1].active_take)
# print(packed)
take2 = rpr.Project().selected_items[1].active_take
RPR.MIDI_SetAllEvts(take2.id, packed, len(packed))
take2.sort_events()
print(int.from_bytes(b'\xff\xff\xff\xff', 'little') - 7846247)
