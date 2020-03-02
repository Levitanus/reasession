import typing as ty
import pickle
import reapy as rpr
import codecs

SECTION = 'levitanus_session_management'


def dumps(key: str, data: object, persist: bool = False) -> None:
    dump = pickle.dumps(data)
    rpr.set_ext_state(
        SECTION, key, codecs.encode(dump, 'base64').decode(), persist=persist
    )


def loads(key: str) -> object:
    dump = rpr.get_ext_state(SECTION, key)
    # print('dump = ', dump)
    return pickle.loads(codecs.decode(dump.encode(), "base64"))
