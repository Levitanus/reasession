import reapy as rpr
import unittest as ut


class TestCase(ut.TestCase):
    @ut.skipIf(not rpr.dist_api_is_enabled(), 'reapy dist api unreacheble')
    def test_api(self) -> None:
        ...
