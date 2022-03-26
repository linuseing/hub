from enum import Enum


class CoreState(Enum):
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
