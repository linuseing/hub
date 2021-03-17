import json
import inspect
import datetime


def default_encoder(msg) -> str:
    return json.dumps(msg, indent=4, cls=ObjectEncoder)


class ObjectEncoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj, "to_json"):
            return self.default(obj.to_json())
        if isinstance(obj, datetime.datetime):
            return obj.__str__()
        if isinstance(obj, datetime.timedelta):
            return obj.__repr__()
        elif hasattr(obj, "__dict__"):
            d = dict(
                (key, value)
                for key, value in inspect.getmembers(obj)
                if not key.startswith("__")
                if not key.startswith("_")
                and not inspect.isabstract(value)
                and not inspect.isbuiltin(value)
                and not inspect.isfunction(value)
                and not inspect.isgenerator(value)
                and not inspect.isgeneratorfunction(value)
                and not inspect.ismethod(value)
                and not inspect.ismethoddescriptor(value)
                and not inspect.isroutine(value)
            )
            return self.default(d)
        elif hasattr(obj, '__repr__'):
            return obj.__repr__()
        return obj
