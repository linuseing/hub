from typing import List

from objects.entity import Entity


class EntityRegistry:

    def __init__(self, core: 'Core'):
        self.core = core
        self.entities: List[Entity] = []
