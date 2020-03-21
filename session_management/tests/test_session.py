import typing as ty
import pytest as pt
import mock
import reapy as rpr
from reapy import reascript_api as RPR
from .. import session as ss
from . import MASTER_PROJ_NAME, SLAVE_PROJECT_NAME

# from time import sleep


@pt.mark.skipif(
    not rpr.dist_api_is_enabled(), reason='not connected to reaper'
)
def test_project():
    pr = ss.Project('test_master')
    assert pr.last_ip == 'localhost'


# @pt.mark.skip
@pt.mark.skipif(
    not rpr.dist_api_is_enabled(), reason='not connected to reaper'
)
@rpr.inside_reaper()
def test_master_out_track():
    m_pr = ss.Project(MASTER_PROJ_NAME)
    s_pr = ss.SlaveProject(SLAVE_PROJECT_NAME, 'localhost')
    m_pr.make_current_project()
    # m_tr = rpr.Track(id='out', project=m_pr)
    # print(s_pr.__module__, s_pr.__qualname__)
    with s_pr.make_current_project():
        s_tr = ss.SlaveInTrack(id='in', project=s_pr)
    o_track = ss.MasterOutTrack(id='out', project=m_pr, target=s_tr)
    # print(type(o_track.project))

    o_childs = o_track.childs
    assert rpr.Track(
        id='no_midi_send', project=ss.Project(MASTER_PROJ_NAME)
    ).id not in o_childs
    assert len(o_childs) == 18

    matched = o_track.match_childs()
    m_id = rpr.Track(id='B4', project=m_pr).id
    with s_pr.make_current_project():
        assert matched[m_id].target == rpr.Track(id='B4', project=s_pr)

    m_id = rpr.Track(id='B3Ch4', project=m_pr).id
    with s_pr.make_current_project():
        assert matched[m_id].target == rpr.Track(id='B3Ch4', project=s_pr)

    m_id = rpr.Track(id='B4Ch1B1', project=m_pr).id
    with s_pr.make_current_project():
        assert matched[m_id].target == rpr.Track(id='B4Ch1', project=s_pr)

    m_id = rpr.Track(id='B2Ch1B1', project=m_pr).id
    with s_pr.make_current_project():
        assert matched[m_id].target == rpr.Track(id='B2Ch1B1', project=s_pr)


@pt.mark.skipif(
    not rpr.dist_api_is_enabled(), reason='not connected to reaper'
)
@rpr.inside_reaper()
@mock.patch.object(rpr, 'connect')
def test_slave_track(mConnect):
    host = '192.168.2.1'
    pr = ss.SlaveProject(id=SLAVE_PROJECT_NAME, ip=host)
    with pr.make_current_project():
        tr = ss.SlaveInTrack(id='in', project=pr)
    rpr.Project(MASTER_PROJ_NAME).make_current_project()
    with tr.connect():
        mConnect.assert_called_with(host)
        assert tr.name == 'in'
    assert tr.name == ''


# @pt.mark.skipif(
#     not rpr.dist_api_is_enabled(), reason='not connected to reaper'
# )
# @rpr.inside_reaper()
# def test_recarm():
#     host = 'localhost'
#     s_pr = ss.SlaveProject(id=SLAVE_PROJECT_NAME, host=host)
#     with s_pr.make_current_project():
#         s_tracks = {}
#         for name in ['B1', 'B1Ch1', 'B4']:
#             s_tracks[name] = ss.Track(rpr.Track(id=name, project=s_pr))
#     m_pr = rpr.Project(id=MASTER_PROJ_NAME)
#     m_pr.make_current_project()
#     o_tracks = {}
#     for name in ['B1', 'B1Ch1', 'B4Ch']
#     # o_tr = ss.MasterOutTrack(rpr.Track(''), slave=s_pr, target: SlaveInTrack)


class MonkeySessTrack:

    def __init__(
        self,
        id: str,
        buses_packed: bool = False,
        buses_unpacked: bool = False
    ) -> None:
        self.id = id
        self.buses_packed = buses_packed
        self.buses_unpacked = buses_unpacked

    @property
    def target(self) -> 'MonkeySessTrack':
        return self._target

    @target.setter
    def target(self, track: 'MonkeySessTrack') -> None:
        self._target = track

    def __repr__(self) -> str:
        return f'Track({self.id}) target = Track({self.target.id})'

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, MonkeySessTrack):
            return False
        if self.id == other.id:
            return True
        return False


def test_child_address():
    ad1 = ss.ChildAddress(1, 2)
    assert ad1.bus == 1
    assert ad1 == (1, 2)
    assert isinstance(ad1, ss.ChildAddress)
    assert ad1 == (1, 0)
    assert ad1 == (0, 2)
    assert ad1 != (0, 1)
    assert ad1 != (2, 2)
    assert ad1 != (1, 2, 3)
    # test for `exists`
    assert ad1 in ((0, 1), (3, 4), (1, 2))


# @mock.patch('ss.Track')
@mock.patch.object(ss, 'Track', MonkeySessTrack)
def test_childs_tree():
    tracks_out = {
        'B1Chall': ss.Track('B1Chall'),
        'B2Chall': ss.Track('B2Chall'),
        'B3Chall': ss.Track('B3Chall', buses_packed=True),
        'B3ChallB1Ch1': ss.Track('B3ChallB1Ch1'),
        'B3ChallB1Ch2': ss.Track('B3ChallB1Ch2'),
        'B4Chall': ss.Track('B4Chall', buses_packed=True),
        'B4ChallB2Ch1': ss.Track('B4ChallB2Ch1'),
        'B4ChallB2Ch2': ss.Track('B4ChallB2Ch2'),
        'B5Chall': ss.Track('B5Chall', buses_packed=True),
        'B5ChallB1Ch1': ss.Track('B5ChallB1Ch1'),
        'B5ChallB2Ch1': ss.Track('B5ChallB2Ch1'),
        'B5ChallB2Ch1B1Chall': ss.Track('B5ChallB2Ch1B1Chall'),
        'B5ChallB2Ch1B2Chall': ss.Track('B5ChallB2Ch1B2Chall'),
    }
    tracks_in = {
        'B1Chall': ss.Track('B1Chall'),
        'B2Chall': ss.Track('B2Chall'),
        'B3Chall': ss.Track('B3Chall', buses_unpacked=True),
        'B3ChallB1Ch1': ss.Track('B3ChallB1Ch1'),
        'B3ChallB1Ch2': ss.Track('B3ChallB1Ch2'),
        'B4Chall': ss.Track('B4Chall'),
        'B5Chall': ss.Track('B5Chall', buses_unpacked=True),
        'B5ChallB2Ch1': ss.Track('B5ChallB2Ch1'),
        'B5ChallB2Ch2': ss.Track('B5ChallB2Ch2'),
    }
    assert tracks_out['B1Chall'].id == "B1Chall"
    tree_out = {
        ss.ChildAddress(1, 0):
            ss.Child(track=tracks_out['B1Chall']),
        ss.ChildAddress(2, 0):
            ss.Child(track=tracks_out['B2Chall']),
        ss.ChildAddress(3, 0):
            ss.Child(
                track=tracks_out['B3Chall'],
                childs={
                    ss.ChildAddress(1, 1):
                        ss.Child(tracks_out['B3ChallB1Ch1']),
                    ss.ChildAddress(1, 2):
                        ss.Child(tracks_out['B3ChallB1Ch2'])
                }
            ),
        ss.ChildAddress(4, 0):
            ss.Child(
                track=tracks_out['B4Chall'],
                childs={
                    ss.ChildAddress(2, 1):
                        ss.Child(tracks_out['B4ChallB2Ch1']),
                    ss.ChildAddress(2, 2):
                        ss.Child(tracks_out['B4ChallB2Ch2'])
                }
            ),
        ss.ChildAddress(5, 0):
            ss.Child(
                track=tracks_out['B5Chall'],
                childs={
                    ss.ChildAddress(1, 1):
                        ss.Child(tracks_out['B5ChallB1Ch1']),
                    ss.ChildAddress(2, 1):
                        ss.Child(
                            tracks_out['B5ChallB2Ch1'],
                            childs={
                                ss.ChildAddress(1, 0):
                                    ss.Child(
                                        tracks_out['B5ChallB2Ch1B1Chall']
                                    ),
                                ss.ChildAddress(2, 0):
                                    ss.Child(
                                        tracks_out['B5ChallB2Ch1B2Chall']
                                    ),
                            }
                        ),
                }
            ),
    }
    tree_in = {
        ss.ChildAddress(1, 0):
            ss.Child(track=tracks_in['B1Chall']),
        ss.ChildAddress(2, 0):
            ss.Child(track=tracks_in['B2Chall']),
        ss.ChildAddress(3, 0):
            ss.Child(
                track=tracks_in['B3Chall'],
                childs={
                    ss.ChildAddress(1, 1): ss.Child(tracks_in['B3ChallB1Ch1']),
                    ss.ChildAddress(1, 2): ss.Child(tracks_in['B3ChallB1Ch2'])
                }
            ),
        ss.ChildAddress(4, 0):
            ss.Child(track=tracks_in['B4Chall']),
        ss.ChildAddress(5, 0):
            ss.Child(
                track=tracks_in['B5Chall'],
                childs={
                    ss.ChildAddress(2, 1): ss.Child(tracks_in['B5ChallB2Ch1']),
                    ss.ChildAddress(2, 2): ss.Child(tracks_in['B5ChallB2Ch2'])
                }
            ),
    }
    init_target = ss.Track('slave_in')
    # tracks matched primary\secondary
    t_m_p, t_m_s = ss.Child.match(tree_out, tree_in, init_target)
    # simple case
    assert t_m_p['B1Chall'].target is tracks_in['B1Chall']
    # complex case
    assert t_m_s['B4ChallB2Ch2'].target is tracks_in['B4Chall']
    # too complex case
    assert t_m_s['B4ChallB2Ch1'].target is tracks_in['B4Chall']
    assert t_m_s['B4ChallB2Ch2'].target is tracks_in['B4Chall']
    assert t_m_s['B5ChallB2Ch1B2Chall'].target is tracks_in['B5ChallB2Ch1']


# @pt.mark.skip
@pt.mark.skipif(
    not rpr.dist_api_is_enabled(), reason='not connected to reaper'
)
@rpr.inside_reaper()
def test_get_childs_tree():
    # test straight
    track = ss.Track(id='B4Ch1', project=ss.Project(MASTER_PROJ_NAME))

    tree = track.get_childs_tree()
    assert tree[(1, 0)].track.name == 'B4Ch1B1'
    assert tree[(3, 0)].track.name == 'B4Ch1B3'
    # test recursive
    track = ss.Track(id='B4', project=ss.Project(MASTER_PROJ_NAME))
    tree = track.get_childs_tree()
    assert tree[(0, 1)].track.name == 'B4Ch1'
    assert tree[(0, 1)].childs[(1, 0)].track.name == 'B4Ch1B1'


@pt.mark.skipif(
    not rpr.dist_api_is_enabled(), reason='not connected to reaper'
)
def test_bus_packed():

    def track(id: str) -> ss.Track:
        return ss.Track(id=id, project=rpr.Project(MASTER_PROJ_NAME))
        # return ss.Track(r_tr)

    tr = track('B2Ch1')
    assert tr.buses_packed is True
    assert tr.buses_unpacked is False
    tr = track('unpacked')
    assert tr.buses_packed is False
    assert tr.buses_unpacked is True
