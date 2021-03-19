from unittest import TestCase

from constants.flow_loader import *

micro_flow_config = [
    {CONFIG: {ACTIVE: True, PASS_THROUGH_BEHAVIOR: PASS_THROUGH_EXCEPT_FORMATTER}},
    {"test.in": {"test_conf": "halloa"}},
    {"test.out": {"test_conf": "ciao"}},
]


class Test(TestCase):
    def test__build_micro_flow(self):
        self.fail()
