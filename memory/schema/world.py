# memory/schema/world.py
from pydantic import BaseModel, Field
from typing import Dict, List


class WorldRule(BaseModel):
    name: str
    description: str
    immutable: bool = True  # 是否绝对规则


class World(BaseModel):
    genre: str
    tech_level: str
    magic_system: str | None = None
    rules: List[WorldRule] = Field(default_factory=list)
