from enum import Enum


class EntityType(Enum):
    LAMP = "Lamp"
    LAMP_RGB = "Lamp-rgb"
    LAMP_BRIGHTNESS = "Lamp-dimmable"
    SWITCH = "Switch"
    COMPOSED = "COMPOSED"
    BLINDS = "Blinds"

    @classmethod
    def types(cls):
        return list(map(lambda x: x.value, cls.__members__.values()))

    @classmethod
    def contains(cls, _type: str) -> bool:
        return _type in cls.types()
