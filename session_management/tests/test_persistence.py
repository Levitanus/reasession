from .. import persistence as prs

import reapy as rpr
from reapy import reascript_api as RPR
import typing as ty
import mock
import pytest as pt


class MyClass:

    def __init__(self, val: int, name: str) -> None:
        self.val = val
        self.name = name

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, MyClass):
            return False
        if other.val == self.val and other.name == self.name:
            return True
        return False


# class MockExtState:

#     def __init__(self) -> None:
#         self.sections: ty.Dict[str, ty.Dict[str, str]] = {}

#     def set(self, section: str, key: str, data: str) -> None:
#         if not hasattr(self.sections, section):
#             self.sections[section] = {}
#         self.sections[section][key] = data

#     def get(self, section: str, key: str) -> str:
#         if not hasattr(self.sections, section):
#             return ''
#         if not hasattr(self.sections[section], key):
#             return ''
#         return self.sections[section][key]

# class MockProjExtState:

#     def __init__(self) -> None:
#         self.sections: ty.Dict[str, ty.Dict[str, str]] = {}

#     def set(self, section: str, key: str, data: str) -> None:
#         if not hasattr(self.sections, section):
#             self.sections[section] = {}
#         self.sections[section][key] = data

#     def get(
#         self, proj: rpr.Project, section: str, key: str, valOutNeedBig: str,
#         valOutNeedBig_sz: int
#     ) -> ty.Tuple[int, rpr.Project, str, str, int]:
#         if not hasattr(self.sections, section):
#             return ''
#         if not hasattr(self.sections[section], key):
#             return ''
#         return self.sections[section][key]


def get_test_data():
    t_1 = MyClass(10, 'some_name')
    t_2 = MyClass(14, 'newname')
    return {
        'val': 42,
        'name': 'Malkolm Reinalds',
        1: t_1,
        2: t_2
    }, "just_string"


@pt.mark.skipif(not rpr.dist_api_is_enabled(), reason='not connected to reaper')
def test_dumps():
    # ext_state = MockExtState()
    # mock.patch('rpr.set_ext_state', ext_state.set)
    # mock.patch('rpr.get_ext_state', ext_state.get)
    data, string = get_test_data()

    prs.dumps('some_key', data)
    prs.dumps('second_key', string)

    assert data == prs.loads('some_key')
    assert string == prs.loads('second_key')
    assert '' == prs.loads('bad_key')
    prs.dumps('key', '')


@pt.mark.skipif(not rpr.dist_api_is_enabled(), reason='not connected to reaper')
def test_porj_dumps():
    # mock.patch('RPR.GetProjExtState')
    # mock.patch('RPR.SetProjExtState')
    # mock.patch('rpr.Project')
    data, string = get_test_data()
    project = rpr.Project()

    prs.proj_dumps(project, 'some_key', data)
    prs.proj_dumps(project, 'second_key', string)

    r_data, r_string = prs.proj_loads(project, 'some_key'), prs.proj_loads(
        project, 'second_key'
    )

    assert data == r_data
    assert string == r_string
    assert '' == prs.proj_loads(project, 'bad_key')
    prs.proj_dumps(project, 'key', '')
