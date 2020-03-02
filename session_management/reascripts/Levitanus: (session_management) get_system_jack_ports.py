# import typing as ty
from session_management import persistence as prs
from session_management.connections.jack_backend import get_jack_ports

if __name__ == '__main__':
    ports = get_jack_ports()
    # print(ports)
    prs.dumps('slave_ports', ports)
    # print(prs.loads('slave_ports'))
