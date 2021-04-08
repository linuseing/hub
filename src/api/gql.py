import re
from typing import TYPE_CHECKING, List, Callable

from hypercorn import Config
from hypercorn.asyncio import serve
from ariadne import QueryType, make_executable_schema, SubscriptionType, MutationType
from ariadne import load_schema_from_path
from ariadne.asgi import GraphQL
from starlette.middleware.cors import CORSMiddleware

from helper.json_encoder import default_encoder
from objects.Context import Context
from objects.Event import Event
from .gql_constants import *

if TYPE_CHECKING:
    from core import Core

VERSION = "0.1"


class GraphAPI:
    query: QueryType = QueryType()
    subscription = SubscriptionType()
    mutations = MutationType()

    def __init__(self, core: "Core"):
        self.core = core
        self.type_defs = load_schema_from_path(f"{core.location}/api/schema/")
        self.add_query("spotifyProgress: String!", self.type_defs)

        self.query.set_field(CORE_VERSION, lambda *_: core.version)
        self.query.set_field(PLUGIN_VERSION, lambda *_: VERSION)
        self.query.set_field(PLUGINS, lambda *_: list(core.plugins.keys()))
        self.query.set_field(VALUE, self.get_value)
        self.query.set_field(
            AVAILABLE_COMPONENTS, lambda *_: list(core.registry.components.keys())
        )
        self.query.set_field(
            AVAILABLE_FORMATTER,
            lambda *_: list(map(lambda x: x.gql(), core.io.formatter)),
        )

        self.query.set_field(ENTITY, self.get_entity)
        self.query.set_field(ENTITIES, self.get_entities)

        self.subscription.set_field(ENTITY, self.entity_subscription)
        self.subscription.set_source(ENTITY, self.entity_subscription_source)

        self.subscription.set_field(VALUE, self.value_subscription)
        self.subscription.set_source(VALUE, self.value_subscription_source)

        self.subscription.set_field(EVENT, self.event_subscription)
        self.subscription.set_source(EVENT, self.event_subscription_source)

        self.mutations.set_field(SET_COMPONENT, self.set_mutation)
        self.mutations.set_field(ACTIVATE_SCENE, self.activate_scene)

    def add_query(self, query_def: str, resolver: Callable):
        query_definition: str = re.findall(
            "(?=type Query)([\s\S]*?)(?<=})", self.type_defs
        )[0]
        self.type_defs = self.type_defs.replace(query_definition, "")

        lines = query_definition.split("\n")
        lines.insert(1, query_def)
        query_definition = "\n".join(lines)

        name = query_def.split("(")[0].split(":")[0].strip()

        self.query.set_field(name, resolver)

        self.type_defs += f"\n{query_definition}"

    def add_mutation(self, mutation_def: str, handler: Callable):
        mutations: str = re.findall(
            "(?=type Mutation)([\s\S]*?)(?<=})", self.type_defs
        )[0]
        self.type_defs = self.type_defs.replace(mutations, "")

        lines = mutations.split("\n")
        lines.insert(1, mutation_def)
        mutations = "\n".join(lines)

        name = mutation_def.split("(")[0].split(":")[0].strip()
        self.mutations.set_field(name, handler)

        self.type_defs += f"\n{mutations}"

    async def setup(self):
        schema = make_executable_schema(
            self.type_defs, self.query, self.subscription, self.mutations
        )
        app = CORSMiddleware(
            GraphQL(schema),
            allow_origins=["*"],
            allow_methods=("GET", "POST", "OPTIONS"),
        )
        conf = Config()
        conf.bind = ["0.0.0.0:8000"]
        await serve(app, conf)

    # ----------- QUERIES -----------

    def get_entity(self, _, __, name: str):
        entity = self.core.registry.get_entities()[name]
        return entity.gql()

    def get_entities(self, *_):
        entities = self.core.registry.get_entities()
        return map(lambda e: e.gql(), entities.values())

    def get_value(self, *_, key=""):
        v = self.core.storage.get_value(key)
        return v if v in BASE_TYPES else default_encoder(v)

    # ----------- SUBSCRIPTIONS -----------

    async def entity_subscription_source(self, *_, name=""):
        async for entity in self.core.registry.state_queue.subscribe():
            if entity.name != name:
                continue
            yield entity.gql()

    @staticmethod
    def entity_subscription(entity, *_, name=""):
        return entity

    async def value_subscription_source(self, *_, key=""):
        value = self.core.storage.get_value(key)
        if type(value) not in BASE_TYPES:
            value = default_encoder(value)
        yield value
        async for value in self.core.storage.subscribe(key):
            if type(value) not in BASE_TYPES:
                value = default_encoder(value)
            yield value

    @staticmethod
    def value_subscription(value, *_, key=""):
        return value

    @staticmethod
    def event_subscription(value, *_):
        return value

    async def event_subscription_source(self, *_):
        async for event in self.core.bus.event_stream.subscribe():  # type: Event
            yield event.gql()

    # ----------- MUTATIONS -----------

    def set_mutation(self, _, info, entity, component, target):
        self.core.registry.call_method(
            entity, component, "set", target, context=Context.admin(external=True)
        )
        return True

    def activate_scene(self, _, info, scene):
        self.core.registry.activate_scene(scene)
        return True
