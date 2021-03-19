from objects.Context import Context


class EventCallbackNotFound(Exception):
    pass


class ConfigError(Exception):
    pass


class ServiceNotFoundError(Exception):
    pass


class FormatterNotFound(Exception):
    pass


class YAMLError(Exception):
    pass


class ComponentNotFound(Exception):
    pass


class FlowNotFound(Exception):
    pass


class EntityNotFound(Exception):
    pass


class NotAuthorizedError(Exception):
    def __init__(self, msg: str = "", context: Context = None, scope: str = ""):
        self.msg = msg
        self.context = context
        self.scope = scope
