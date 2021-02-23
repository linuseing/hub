from objects.component import Component


class Entity:

    def __init__(self):
        self.components: list[Component] = []
        self.settings: dict[str, any] = []
