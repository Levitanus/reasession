# import typing as ty
from session_management import persistence as prs
from .jack_backend import get_jack_ports

if __name__ == '__main__':
    prs.dumps('slave_ports', get_jack_ports())
    # print(prs.loads('slave_ports'))
