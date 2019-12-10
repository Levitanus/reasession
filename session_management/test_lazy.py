import reapy as rp
from time import sleep
import asyncio as aio
from threading import Thread
import typing as ty
from random import randint

i: int = 0
rp.clear_console()


async def msleep(sec: float) -> None:
    sleep(sec)
    return None


async def long(sec: float = 1) -> None:
    global i
    rp.print(i)
    await msleep(sec)


def long_n(sec: float = 1) -> None:
    global i
    rp.print(i)
    sleep(sec)


class LongThread(Thread):
    data: int

    def run(self) -> None:
        self.data = randint(1, 10)
        global i
        long_n(5)
        i = 6
        rp.defer(rp.print, 'finishing')

    def get_data(self) -> int:
        return self.data


threads: ty.List[LongThread] = []
# very_long = Thread(target=sleep, args=(10, ), daemon=True)
# very_long.start()

tr = LongThread(daemon=True)
threads.append(tr)
tr.start()


def main() -> None:
    global i
    global threads
    if i < 5:
        rp.defer(main)
    # i += 1
    return


def join_all() -> None:
    global threads
    for tr in threads:
        tr.join()
    # very_long.join()


main()

rp.at_exit(rp.print, 'finished')
