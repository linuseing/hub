from objects.User import User


class Context:
    """Represents the context in which actions like events happen."""

    def __init__(self, user: User = None, remote: bool = False) -> None:
        self.user: User = user or User.new()
        self.remote = remote

    def authorize(self, scope, permission) -> bool:
        """checks the scope and returns if the User is authorized"""
        return self.user.authorize(scope, permission)

    def __repr__(self) -> str:
        return f'<Context {self.user} | {"remote" if self.remote else "internal"}>'

    @staticmethod
    def default() -> "Context":
        return Context()

    @staticmethod
    def admin(external=False) -> "Context":
        return Context(user=User.new_admin(), remote=external)
