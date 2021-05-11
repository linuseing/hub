from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Episode:
    name: str
    podcast: str
    uri: str


@dataclass
class Thumbnail:
    low: str
    medium: str
    large: str


@dataclass
class Show:
    name: str
    id: str

    episodes: Optional[List[Episode]] = None

    @property
    def uri(self) -> str:
        return f"spotify:show:{self.id}"
