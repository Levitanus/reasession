"""Module for setting IP for slave server.
If run as reascript - removes IP fromo reaper and asks user to reassign.
Can be used as function:
    from set_slave_ip import cnoose_ip
    if not rpr.has_ext_state(EXT_SECTION, ADDRESS_KEY_SLAVE):
        host = cnoose_ip()
        if host is None:
            rpr.show_message_box(text='cannot run slave',
                                title='error',
                                type="ok")
            raise RuntimeError('cannot run slave')
        HOST = host
    else:
        HOST = rpr.get_ext_state(EXT_SECTION, ADDRESS_KEY_SLAVE)
"""

import typing as ty
import netifaces as nip
import reapy as rpr
from common import log
from config import EXT_SECTION, ADDRESS_KEY_SLAVE


def cnoose_ip() -> ty.Optional[str]:
    """Ask user to choose IP for slave server."""
    hard = ty.cast(ty.List[str], nip.interfaces())
    log(hard)
    addresses = [
        nip.ifaddresses(iface)[nip.AF_INET][0]['addr'] for iface in hard
    ]
    log(*addresses)
    rpr.delete_ext_state(EXT_SECTION, ADDRESS_KEY_SLAVE, persist=True)
    for addr in addresses:
        response = rpr.show_message_box(
            text=f"""slave server can listen of dollowing ips:
            {addresses}
            Do you want to use {addr}?
            (other will be prompted if you refuse)""",
            title="choose slave IP",
            type="yes-no"
        )
        if response == 'yes':
            rpr.set_ext_state(EXT_SECTION, ADDRESS_KEY_SLAVE, addr)
            return rpr.get_ext_state(EXT_SECTION, ADDRESS_KEY_SLAVE)

    rpr.show_message_box(text='no IP set', title='status', type="ok")
    return None


if __name__ == '__main__':
    cnoose_ip()
