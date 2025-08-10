from __future__ import annotations

from pydantic import BaseModel


class CharacterDTO(BaseModel):
    id: int
    user_id: int
    name: str
    cls: str
    level: int
    xp: int
    map: str
    x: int
    y: int
    hp: int
    mp: int



