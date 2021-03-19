from unittest import TestCase
from src.objects.User import User


class TestUser(TestCase):
    def create_test_user(self, scopes):
        return User(name="Test user", scopes=scopes)

    def test_authorize_admin(self):
        admin = User.new_admin()
        if admin.authorize("test.test", ["r"]):
            self.fail()

    def test_authorize_pleb(self):
        user = self.create_test_user({})
        if user.authorize("test.test", "r"):
            self.fail()

    def test_authorize_wildcard(self):
        user = self.create_test_user({"test.*": ["r", "w"]})
        if not user.authorize("test.test1", "r"):
            self.fail()

        if not user.authorize("test", "w"):
            self.fail()

    def test_new_admin(self):
        admin = User.new_admin()
