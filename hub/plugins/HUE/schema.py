import logging
from typing import Dict

from voluptuous import Schema, Required, MultipleInvalid


LOGGER = logging.getLogger("hue")


CONFIG_SCHEMA = Schema({
    Required("host"): str
})


def test_config(config: Dict) -> bool:
    try:
        CONFIG_SCHEMA(config)
        return True
    except MultipleInvalid as e:
        for missing in e.errors:
            LOGGER.error(f"Missing config entry: {missing.path}")
        return False
