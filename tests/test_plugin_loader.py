from unittest import TestCase
from plugin_loader import build_doc
from objects.OutputService import ServiceDocs, Arg


def test(self, _, test1: str = "", test2: bool = True):
    """Hallo
    Test method
    :param self:
    :param _:
    :param test1: test param
    :param test2: test2 param
    :return:
    """
    pass


test_doc = ServiceDocs(
    description="Hallo\nTest method",
    args={
        "test": Arg(type=str, doc="test param", default=""),
        "test2": Arg(type=str, doc="test2 param", default=True),
    },
)


class Test(TestCase):
    def test_build_doc(self):
        print(build_doc(test))

        assert build_doc(test), test_doc
