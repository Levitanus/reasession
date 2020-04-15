import reapy as rpr
from reapy import reascript_api as RPR
import typing as ty
import typing_extensions as te
import json
# from reaper_python import *

# from simple_test_data import data as test_data

MidiBuf = te.TypedDict(
    'MidiBuf', {
        'qn': float,
        'bus': float,
        'buf': ty.List[float]
    }
)

key_fx_idx = 'render_midi_fx_idx'
key_track_idx = 'render_midi_track_idx'
key_proj_idx = 'render_midi_proj_idx'

key_result = 'render_midi_output'

SECTION = 'REASESSION'

fx_name = 'levitanus(reasession)_render_midi'


def add_jsfx_to_track(track: rpr.Track) -> rpr.FX:
    global fx_name
    return track.add_fx(fx_name)


@rpr.inside_reaper()
def get_midi_from_track(
    track: rpr.Track, project_idx: ty.Optional[int] = None
) -> str:
    global SECTION, key_fx_idx, key_track_idx, key_proj_idx, key_result
    pr = track.project

    if project_idx is None:
        for idx, proj in enumerate(rpr.get_projects()):
            if proj.id == pr.id:
                project_idx = idx
    for idx, tr in enumerate(pr.tracks):
        if tr.id == track.id:
            track_idx = idx

    rpr.set_ext_state(SECTION, key_proj_idx, str(project_idx))
    rpr.set_ext_state(SECTION, key_track_idx, str(track_idx))
    # fx = add_jsfx_to_track(track)
    fx = track.fxs[fx_name]
    rpr.set_ext_state(SECTION, key_fx_idx, str(fx.index))
    # print(fx)
    # print(project_idx, track_idx, fx.index)
    command_id = rpr.get_command_id(
        "_RSf3f54c28105cef27e0d62a326647e71bd48d882a"
    )
    assert isinstance(command_id, int)
    # print(command_id)
    rpr.perform_action(command_id)
    # rpr.arm_command()
    raw_midi = rpr.get_ext_state(SECTION, key_result)
    return raw_midi


def create_item_from_raw_midi(track: rpr.Track, raw_midi: str) -> rpr.Item:
    m_list = ty.cast(ty.List[MidiBuf], json.loads(raw_midi))
    s_pos = m_list[0]['qn']
    e_pos = m_list[-1]['qn'] + 0.1
    s_pos_b, e_pos_b = s_pos, e_pos
    pr = track.project
    s_pos = pr.beats_to_time(s_pos)
    e_pos = pr.beats_to_time(e_pos)
    item = track.add_midi_item(start=s_pos, end=e_pos)
    take = item.active_take
    # take = item.add_take()
    print(s_pos_b, e_pos_b, s_pos, e_pos)
    take.add_note(s_pos+1, s_pos+2, 60)
    take.add_sysex(s_pos+2, [0xf0, 0x90, 60, 80, 0xf7])
    print(take.notes[0])
    # take.sort_events()
    # for evnt in m_list:

    return item


pr = rpr.Project()
tr = pr.selected_tracks[0]
# print(add_jsfx_to_track(tr))
# print(get_midi_from_track(tr))
raw_midi = rpr.get_ext_state(SECTION, key_result)
# print(raw_midi)
# unserialized = ty.cast(ty.List[MidiBuf], json.loads(raw_midi))
# print(unserialized)

create_item_from_raw_midi(tr, raw_midi)
