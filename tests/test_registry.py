from unittest import TestCase
from src.objects.User import User
from src.entity_registry import EntityRegistry

lamp_config = """
type: Lamp
control: test
switch:
  t: decke
brightness:
  t: decke
color:
  t: decke
"""


class TestRegistry(TestCase):

    def test_create(self):
        R = EntityRegistry(None)
