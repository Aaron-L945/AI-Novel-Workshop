# memory/schema/character.py
from pydantic import BaseModel
from typing import List, Dict

class CharacterCore(BaseModel):
    name: str
    gender: str | None = None
    personality: List[str]
    values: List[str]        # 世界观、信念
    fears: List[str] = []

class CharacterState(BaseModel):
    alive: bool = True
    location: str | None = None
    physical_status: List[str] = []
    mental_status: List[str] = []

class Character(BaseModel):
    core: CharacterCore          # 几乎不变
    state: CharacterState        # 会变
    first_appearance_chapter: int
