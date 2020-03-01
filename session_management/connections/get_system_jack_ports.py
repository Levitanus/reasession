import typing as ty
from session_management import persistence as prs

from .backend import HardwarePorts, SystemJackPort, JackPortDump


def get_ports() -> ty.List[SystemJackPort]:
    hwp = HardwarePorts(is_master=False)
    return ty.cast(ty.List[SystemJackPort], hwp._reaper_ports)


def dump_ports(ports: ty.List[SystemJackPort]) -> ty.List[JackPortDump]:
    out = []
    for port in ports:
        out.append(JackPortDump(port))
    return out


def get_ports_dump() -> ty.List[JackPortDump]:
    return prs.loads('slave_ports')


if __name__ == '__main__':
    prs.dumps('slave_ports', dump_ports(get_ports()))
    print(prs.loads('slave_ports'))
