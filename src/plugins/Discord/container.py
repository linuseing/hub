import dataclasses
from typing import Optional


@dataclasses.dataclass
class ActiveUser:
    name: str
    status: str
    avatar_url: str
    game: Optional[str] = None

