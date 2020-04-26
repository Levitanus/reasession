import mock
import pytest as pt
import reapy as rpr

from reasession.session import session as sess
from reasession import session as ss
from reasession.connections.jack_backend import Connector


class MonkeyHost(ss.Host):

    def __init__(self, ip: ss.HostIP) -> None:
        self.ip = ip


@pt.mark.skipif(not rpr.dist_api_is_enabled(), reason='not connected')
@mock.patch.object(ss, 'Host', MonkeyHost)
def test_sess_hosts():
    my_sess = sess.Session(ss.Project('test_master'))
    my_sess._hosts.add(ss.Host('192.168.3.45'))
    assert my_sess._hosts == set(
        [ss.Host('192.168.3.45'),
         ss.Host('localhost')]
    )
    my_sess.hosts_check()
    assert ss.Host('192.168.3.45') not in my_sess._hosts


@pt.mark.skipif(not rpr.dist_api_is_enabled(), reason='not connected')
def test_slaves_handling():
    my_sess = sess.Session(ss.Project('test_master_persistent'))
    slave1 = ss.projects.SlaveProject('test_slave')
    slave2 = ss.projects.SlaveProject('test_slave2')
    m_pr = my_sess.master
    sl1_tr, sl2_tr = [
        ss.tracks.Track(name, m_pr) for name in ('slave1', 'slave2')
    ]
    # my_sess.slaves = {sl1_tr.GUID: slave1, sl2_tr.GUID: slave2}
    slaves_keys = tuple(my_sess.slaves.keys())
    assert slaves_keys == (sl1_tr.GUID, sl2_tr.GUID)


@pt.mark.skipif(not rpr.dist_api_is_enabled(), reason='not connected')
def test_slave_state_tracking():
    m_sess = sess.Session(ss.Project('test_master_persistent'))
    slave1 = ss.projects.SlaveProject('test_slave')
    slave2 = ss.projects.SlaveProject('test_slave2')

    assert m_sess.slaves[slave1].is_accessible
    assert m_sess.slaves[slave2].is_accessible

    slave2.close()

    assert not m_sess.slaves[slave2].is_accessible
    m_sess.slaves.open(slave2)
    assert slave2.is_accessible
