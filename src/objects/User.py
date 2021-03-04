from typing import Dict, List


class User:

    def __init__(self, name: str = "Linus", is_admin=False, scopes: Dict[str, List[str]] = {}):
        self.name = name
        self.admin = is_admin
        self.scopes: Dict[str, List[str]] = scopes

    def authorize(self, scope: str, permission: str) -> bool:
        if permissions := self.scopes.get(scope, False):
            if permission in permissions:
                return True
        path = ''
        for fragment in scope.split('.'):
            path += f'.{fragment}'
            if permissions := self.scopes.get(path[1:], False):
                if permission in permissions or '*' in permissions:
                    return True
            if permissions := self.scopes.get(f'{path}.*'[1:], False):
                if permission in permissions or '*' in scope:
                    return True
        if permissions := self.scopes.get('*', False):
            if permission in permissions or '*' in permissions:

                return True
        return False

    def __repr__(self):
        return f'<{self.name}{f" (admin)" if self.admin else ""}>'

    @staticmethod
    def new_admin():
        return User(is_admin=True, scopes={'*': ['*']})

    @staticmethod
    def new():
        return User()

