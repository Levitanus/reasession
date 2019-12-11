import reapy as rpr
from time import sleep
from reaper_python import *

# rpr.clear_console()

rpr.print('\n\nstart')


def exiting() -> None:
    rpr.print('exiting....')
    sleep(2)
    rpr.print('exited')


rpr.at_exit(exiting)


def main() -> None:
    rpr.print('main')


main()
