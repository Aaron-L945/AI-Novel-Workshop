# memory/schema/meta.py
from pydantic import BaseModel
from datetime import datetime

class CanonMeta(BaseModel):
    version: int = 1
    last_updated_chapter: int
    updated_at: datetime
