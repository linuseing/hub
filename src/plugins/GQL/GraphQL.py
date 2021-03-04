from typing import TYPE_CHECKING, Dict

import uvicorn
from ariadne import gql, QueryType, make_executable_schema, ObjectType
from ariadne import load_schema_from_path
from ariadne.asgi import GraphQL

from plugin_api import plugin, run_after_init
from .constants import *

if TYPE_CHECKING:
    from core import Core

VERSION = '0.1'


@plugin('GQL')
class GraphAPI:
    query: QueryType = QueryType()

    def __init__(self, core: 'Core', config: Dict = None):
        self.core = core
        self.type_defs = load_schema_from_path(f"{core.location}/plugins/GQL/schema/")

        self.query.set_field(CORE_VERSION, self.version)
        self.query.set_field(PLUGIN_VERSION, lambda *_: VERSION)

        self.query.set_field('entity', self.get_entity)
        self.query.set_field(ENTITIES, self.get_entity)
        entity = ObjectType("Entity")
        entity.set_field('name', lambda obj, *_: obj.name)

    @run_after_init
    async def setup(self):
        schema = make_executable_schema(self.type_defs, self.query)
        app = GraphQL(schema, debug=True)
        self.core.add_job(
            lambda: uvicorn.run(app, host="127.0.0.1", port=5000, log_level="error")
        )

    def get_entity(self, a, b, name: str):
        entity = self.core.registry.get_entities()[name]
        return entity

    def get_entities(self, *_):
        entities = self.core.registry.get_entities()
        return ['test']

    def version(self, *_) -> str:
        return self.core.version
