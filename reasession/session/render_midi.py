import reapy as rpr
import typing as ty
import typing_extensions as te
import json
import os

from reasession.config import EXT_SECTION

MidiBuf = te.TypedDict(
    'MidiBuf', {
        'qn': float,
        'bus': int,
        'buf': ty.List[int],
    }
)
MidiNote = te.TypedDict(
    'MidiNote', {
        'start': float,
        'end': float,
        'note': int,
        'channel': int,
        'velocity': int
    }
)
RenderSettings = te.TypedDict(
    'RenderSettings', {
        'value': ty.Dict[str, float],
        'string': ty.Dict[str, str]
    }
)


class MidiRenderer:
    """Renders midi and can past it to different tracks (and hosts).

    Note
    ----
    Renders midi on track as it comes to the end of FxChain
    """

    key_fx_idx = 'render_midi_fx_idx'
    key_track_idx = 'render_midi_track_idx'
    key_proj_idx = 'render_midi_proj_idx'

    key_result = 'render_midi_output'

    fx_name = 'levitanus(reasession)_render_midi'

    def __init__(self) -> None:
        with rpr.inside_reaper():
            self.get_command_id: int = rpr.get_command_id(  # type:ignore
                "_RSf3f54c28105cef27e0d62a326647e71bd48d882a"
            )
            assert isinstance(self.get_command_id, int),\
                'cannot load render_midi.lua'

    def add_jsfx_to_track(self, track: rpr.Track) -> rpr.FX:
        return track.add_fx(self.fx_name)

    def _deserialize_buffer(self, raw_midi: str) -> ty.List[MidiBuf]:
        m_list = json.loads(raw_midi)
        midi_buf: ty.List[MidiBuf] = []
        for item in m_list:
            midi_buf.append(
                MidiBuf(
                    qn=item['qn'],
                    bus=int(item['bus']),
                    buf=[int(i) for i in item['buf']],
                )
            )
        return midi_buf

    def get_midi_from_track(
        self, track: rpr.Track, project_idx: ty.Optional[int] = None
    ) -> ty.List[MidiBuf]:
        pr = track.project

        project_idx = self._get_project_idx(pr, project_idx)
        for idx, tr in enumerate(pr.tracks):
            if tr.id == track.id:
                track_idx = idx

        rpr.set_ext_state(EXT_SECTION, self.key_proj_idx, str(project_idx))
        rpr.set_ext_state(EXT_SECTION, self.key_track_idx, str(track_idx))
        # fx = add_jsfx_to_track(track)
        fx = track.fxs[self.fx_name]
        rpr.set_ext_state(EXT_SECTION, self.key_fx_idx, str(fx.index))

        self._get_from_lua()
        raw_midi = rpr.get_ext_state(EXT_SECTION, self.key_result)
        if raw_midi == '':
            raise RuntimeError('no midi_data got from the track')
        return self._deserialize_buffer(raw_midi)

    def _get_from_lua(self) -> None:
        """For profiling needs."""
        rpr.perform_action(self.get_command_id)

    def _get_project_idx(
        self, pr: rpr.Project, project_idx: ty.Optional[int] = None
    ) -> int:
        if project_idx is not None:
            return project_idx
        for idx, proj in enumerate(rpr.get_projects()):
            if proj.id == pr.id:
                return idx
        raise RuntimeError('cannot find project {pr.id} on the host')

    def build_midi_on_track(
        self,
        track: rpr.Track,
        midi_buf: ty.List[MidiBuf],
        erase_items: bool = True
    ) -> None:
        prefix = [0xFF, 0x52, 0x50, 0x62]
        if erase_items:
            for itm in track.items:
                itm.delete()
        i_s, i_e = (i['qn'] for i in (midi_buf[0], midi_buf[-1]))
        item = track.add_midi_item(
            start=i_s - 0.1 if i_s > 0.1 else 0, end=i_e + 0.1, quantize=True
        )

        take = item.active_take
        ppqs = take.map(
            'beat_to_ppq', iterables={'beat': [it['qn'] for it in midi_buf]}
        )
        end_buf: ty.List[rpr.MIDIEventDict] = []

        for idx, ziped in enumerate(zip(midi_buf, ppqs)):
            msg, ppq = ziped
            if msg['bus'] != 0:
                buf = [
                    0xf0, *prefix,
                    int(msg['bus']), *list(int(bt) for bt in msg['buf']), 0xf7
                ]
            else:
                buf = msg['buf']
            end_evt: rpr.MIDIEventDict = {
                'ppq': ppq,
                'selected': False,
                'muted': False,
                'cc_shape': rpr.CCShapeFlag.square,
                'buf': buf
            }
            end_buf.append(end_evt)
        take.set_midi(end_buf)

    def render_tracks(self, tracks: ty.List[rpr.Track]
                      ) -> ty.Dict[str, ty.List[MidiBuf]]:

        pattern = 'temp_for_render_midi'
        resource_path = rpr.get_resource_path()
        project = tracks[0].project
        selected_tracks = list(project.selected_tracks)
        for track in tracks:
            self.add_jsfx_to_track(track)

        original_settings = self._get_render_settings(project)
        new_settings: RenderSettings = {
            'value':
                {
                    'RENDER_SETTINGS': 3.0,
                    'RENDER_BOUNDSFLAG': 1,
                    'RENDER_CHANNELS': 1,
                    'RENDER_ADDTOPROJ': 0,
                    'RENDER_SRATE': 0,
                },
            'string':
                {
                    'RENDER_FILE': resource_path,
                    'RENDER_PATTERN': pattern,
                    'RENDER_FORMAT': 'vggo',
                }
        }
        project.selected_tracks = tracks
        self._set_render_settings(new_settings, project)
        self._render_it()
        self._set_render_settings(original_settings, project)
        self._remove_rendered_audio(resource_path, pattern, tracks)
        project.selected_tracks = selected_tracks
        midi = {}
        for track in tracks:
            midi[track.id] = self.get_midi_from_track(track)
        return midi

    def _render_it(self) -> None:
        render_action = 42230
        rpr.perform_action(render_action)

    def _remove_rendered_audio(
        self, resource_path: str, pattern: str, tracks: ty.List[rpr.Track]
    ) -> None:
        for idx, track in enumerate(tracks):
            idx_str = '' if len(tracks) == 1 else f'-{idx+1:03d}'
            filename = f'{os.path.join(resource_path, pattern)}{idx_str}.ogg'
            os.remove(filename)

    def _set_render_settings(
        self, new_settings: RenderSettings, project: rpr.Project
    ) -> None:
        for key, val in new_settings['value'].items():
            project.set_info_value(key, val)
        for key, string in new_settings['string'].items():
            project.set_info_string(key, string)

    def _get_render_settings(self, project: rpr.Project) -> RenderSettings:
        value_keys = [
            'RENDER_SETTINGS', 'RENDER_BOUNDSFLAG', 'RENDER_CHANNELS',
            'RENDER_SRATE', 'RENDER_STARTPOS', 'RENDER_ENDPOS',
            'RENDER_TAILFLAG', 'RENDER_TAILMS', 'RENDER_ADDTOPROJ',
            'RENDER_DITHER'
        ]
        string_keys = ['RENDER_FILE', 'RENDER_PATTERN', 'RENDER_FORMAT']
        out: RenderSettings = {'value': {}, 'string': {}}
        for key in value_keys:
            out['value'][key] = project.get_info_value(key)
        for key in string_keys:
            out['string'][key] = project.get_info_string(key)
        return out
