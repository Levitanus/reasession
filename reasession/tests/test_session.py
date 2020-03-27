import mock
import pytest as pt
import reapy as rpr

from ..session import session as sess
from .. import session as ss
from ..connections.jack_backend import Connector


class MonkeyHost(ss.Host):

    def __init__(self, ip: ss.HostIP) -> None:
        self.ip = ip


@pt.mark.skipif(
    not rpr.dist_api_is_enabled(), reason='not connected to reaper'
)
@mock.patch.object(ss, 'Host', MonkeyHost)
def test_sess_hosts():
    my_sess = sess.Session(ss.Project('test_master'))
    my_sess._hosts.add(ss.Host('192.168.3.45'))
    assert my_sess._hosts == set(
        [ss.Host('192.168.3.45'),
         ss.Host('localhost')]
    )
    my_sess.hosts_check()
    assert ss.Host('localhost') not in my_sess._hosts
