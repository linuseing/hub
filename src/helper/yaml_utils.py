import os
import yaml
import logging

from collections import defaultdict

from exceptions import YAMLError

_LOGGER = logging.getLogger(__name__)


class SafeLineLoader(yaml.SafeLoader):
    """Loader class that keeps track of line numbers."""

    def compose_node(self, parent: yaml.nodes.Node, index: int) -> yaml.nodes.Node:
        """Annotate a node with the first line it was seen."""
        last_line: int = self.line
        node: yaml.nodes.Node = super(SafeLineLoader, self).compose_node(parent, index)
        node.__line__ = last_line + 1  # type: ignore
        return node


def load_yaml(fname: str):
    """Load a YAML file."""
    try:
        with open(fname, encoding="utf-8") as conf_file:
            # If configuration file is empty YAML returns None
            # We convert that to an empty dict
            return yaml.load(conf_file, Loader=SafeLineLoader)
    except FileNotFoundError:
        return None
    except yaml.YAMLError as exc:
        raise YAMLError()
    except UnicodeDecodeError as exc:
        _LOGGER.error("Unable to read file %s: %s", fname, exc)
        raise YAMLError(exc)


def for_yaml_in(dir_path: str, def_dict=False, def_lambda=lambda: {}):
    if not dir_path.endswith("/"):
        dir_path += "/"
    for file in os.listdir(dir_path):
        if file.endswith(".yaml"):
            _yaml = load_yaml(os.path.join(dir_path + file))
            if def_dict:
                _yaml = defaultdict(def_lambda, _yaml if _yaml is not None else {})
            yield _yaml, file


def save_to_yaml(file: str, data: dict):
    with open(file, 'w') as outfile:
        yaml.dump(data, outfile, default_flow_style=False)
