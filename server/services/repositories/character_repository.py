from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.character import Character
from sqlalchemy import update


async def get_by_user(session: AsyncSession, user_id: int) -> Optional[Character]:
    result = await session.execute(select(Character).where(Character.user_id == user_id))
    return result.scalar_one_or_none()


async def create_default(session: AsyncSession, user_id: int) -> Character:
    char = Character(user_id=user_id, name="Adventurer", class_name="novice")
    session.add(char)
    await session.flush()
    return char


async def update_state(session: AsyncSession, char: Character, *, x: int, y: int, hp: int, mp: int) -> None:
    char.x = x
    char.y = y
    char.hp = hp
    char.mp = mp
    await session.flush()


async def update_state_by_id(session: AsyncSession, char_id: int, *, x: int, y: int, hp: int, mp: int) -> None:
    await session.execute(
        update(Character)
        .where(Character.id == char_id)
        .values(x=x, y=y, hp=hp, mp=mp)
    )
    await session.flush()


