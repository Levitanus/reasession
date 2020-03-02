import reapy as rpr
from reapy import reascript_api as RPR
import typing as ty
import typing_extensions as te

from session_management import persistence as prs


def get_slave_ports(slave: str) -> ty.Dict[str, object]:
    with rpr.connect(slave):
        with rpr.inside_reaper():
            a_id = RPR.NamedCommandLookup(
                '_RSb8cfde53a13f3f5f4f997524327c13ab958a8cb6'
            )
            rpr.perform_action(a_id)
            return prs.loads('slave_ports')


if __name__ == '__main__':
    ports = [port.get_conn_dict() for port in get_slave_ports('192.168.2.2')]
    print(ports, type(ports[0]), sep='\n-------------------\n')
