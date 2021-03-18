from typing import Dict

from objects.entity import Entity


COMPONENT_TYPE_MAPPING = {}


def legacy_entity(entity: Entity) -> Dict:
    return {
        'name': entity.name,
        'type': entity.type,
        'tags': [],
        'settings': entity.settings,
        'attributes': map(lambda x: {
            'name': x.name,
            'type': COMPONENT_TYPE_MAPPING[x.type],
            'state': x.state,
            'settings': x.settings
        }, entity.components.values())
    }


def success(id):
    return {"id": id, "success": True}


def error(_id, _error=""):
    return {"id": _id, "success": False, "error": _error}


def event_message(id, event):
    return {"id": id, "type": "event", "event": event}


def data_message(id, entry, value):
    return {"id": id, "type": "data", "entry": entry, "value": value}


def values_message(id, values):
    return {"id": id, "type": "data", "values": values}


def entity_created_message(id, entity: Entity):
    return {"id": id, "entity": legacy_entity(entity), "type": "created"}


def entity_updated_message(id, entity: Entity):
    return {"id": id, "entity": legacy_entity(entity), "type": "update"}
