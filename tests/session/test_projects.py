import mock
import reasession.session as ss
from reasession.session import projects as spr
from reasession.config import EXT_SECTION
import reapy as rpr
import pytest as pt


@pt.mark.skipif(not rpr.dist_api_is_enabled(), reason='not connected')
def test_host():
    assert spr.Host('localhost') == spr.Host('localhost')
    with pt.raises(rpr.errors.DisabledDistAPIError):
        spr.Host('192.168.23.13')


@pt.mark.skipif(not rpr.dist_api_is_enabled(), reason='not connected')
def test_project():
    gen = spr.Project('generic')
    assert gen._guid is None
    gen_guid = gen.GUID
    assert gen_guid == gen.get_ext_state(EXT_SECTION, 'guid', pickled=False)
    assert gen_guid != gen.GUID_new()
    assert gen_guid != gen.GUID
    assert gen_guid != gen._guid

    assert gen.last_ip == ss.HostIP('localhost')
    assert gen.host == spr.Host('localhost')
    assert gen.last_ip == ss.HostIP('localhost')
    assert gen.last_ip == str(ss.HostIP('localhost'))

    assert gen.is_master is False
    # spr.Project('test_master').is_master = True
    assert spr.Project('test_master').is_master is True


class MonkeyHost(ss.Host):

    def __init__(self, ip: ss.HostIP) -> None:
        self.ip = ip


@pt.mark.skipif(not rpr.dist_api_is_enabled(), reason='not connected')
@mock.patch.object(spr, 'Host', MonkeyHost)
def test_slave_project():
    sl = spr.SlaveProject('test_slave')
    sl._id = None
    with pt.raises(ss.SessionError):
        sl.name
    sl1 = spr.SlaveProject('test_slave')
    sl1.GUID_new()
    sl1._id = None
    with pt.raises(ss.SlaveUnacessible):
        sl1.name
    assert sl1.is_accessible is False
    sl1.id = ('test_slave')  # type:ignore
    assert sl1.is_accessible is True
    host = spr.Host(ss.HostIP('192.168.4.5'))
    sl1.host = host
    assert sl1.is_accessible is False
    assert sl1.freezed_state is False
