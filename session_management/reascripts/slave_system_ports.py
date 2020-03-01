import reapy as rpr
from session_management.connections import get_system_jack_ports as gsjp

if __name__ == '__main__':
    prs.dumps('slave_ports', dump_ports(get_ports()))
    rpr.print(prs.loads('slave_ports'))
