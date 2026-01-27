# memory/schema/system.py
from pydantic import BaseModel
from typing import List

class Artifact(BaseModel):
    name: str
    origin: str
    abilities: List[str]
    restrictions: List[str]
    owner: str | None = None
