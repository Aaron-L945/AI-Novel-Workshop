# memory/schema/timeline.py
from pydantic import BaseModel
from typing import List, Literal


class CanonEvent(BaseModel):
    chapter: int
    description: str
    involved_characters: List[str]
    irreversible: bool = True  # 是否不可逆
    event_type: Literal[
        "death", "injury", "revelation", "relationship", "world_change", "plot", "other"
    ]
