# memory/schema/location.py
from pydantic import BaseModel
from typing import List

class Location(BaseModel):
    name: str
    description: str
    properties: List[str] = []
    connected_locations: List[str] = []
