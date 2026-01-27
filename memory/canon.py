# memory/canon.py

from datetime import datetime
from pydantic import BaseModel, Field
from memory.schema.world import World
from memory.schema.character import Character
from memory.schema.timeline import CanonEvent
from memory.schema.location import Location
from memory.schema.system import Artifact
from memory.schema.meta import CanonMeta
from typing import Dict, List


class CanonMemory(BaseModel):
    world: World = Field(
        default_factory=lambda: World(
            genre="", tech_level="", magic_system=None, rules=[]
        )
    )

    characters: Dict[str, Character] = Field(default_factory=dict)
    timeline: List[CanonEvent] = Field(default_factory=list)
    locations: Dict[str, Location] = Field(default_factory=dict)
    artifacts: Dict[str, Artifact] = Field(default_factory=dict)

    meta: CanonMeta = Field(
        default_factory=lambda: CanonMeta(
            version=1, last_updated_chapter=0, updated_at=datetime.utcnow()
        )
    )

    def read(self):
        return self.model_dump()

    def write(self, *args, **kwargs):
        raise PermissionError("Canon memory is read-only")
