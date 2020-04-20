import reapy as rpr
# from reapy import reascript_api as RPR
from reasession.session import render_midi as rm
import time
import cProfile
import pstats
from pstats import SortKey

pr = rpr.Project()
# tr = rpr.Project().tracks[0]
# tr2 = rpr.Project().tracks[1]
rd = rm.MidiRenderer()
# # rd.add_jsfx_to_track(tr)
# # midi = rd.get_midi_from_track(tr, 0)
# raw_midi = rpr.get_ext_state('REASESSION', 'render_midi_output')
# rd.build_midi_on_track(tr2, rd._deserialize_buffer(raw_midi))
midi = rd.render_tracks([pr.tracks[0]])


@rpr.inside_reaper()
def build():
    strt = time.time()
    # for tr, buf in zip(pr.tracks[2:3], midi.values()):
    #     rd.build_midi_on_track(tr, buf)
    rd.build_midi_on_track(pr.tracks[2], midi[pr.tracks[0].id])
    print(time.time() - strt)


# print(os.path.join(res, pat, 'ogg'))

cProfile.run('build()', filename='raw', sort=1)
p = pstats.Stats('raw')
(p.strip_dirs().sort_stats(
    # 'time',
    'cumulative'
).print_stats())
