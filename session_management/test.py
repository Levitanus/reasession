from time import sleep

from networking import Discovery
from networking import DEF_PORT


def callback() -> None:
    pass


disc = Discovery(DEF_PORT, callback)


def main() -> None:
    disc.cb()
    sleep(.3)
    main()


main()
