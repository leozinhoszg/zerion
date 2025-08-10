from __future__ import annotations

from typing import Optional

from passlib.hash import bcrypt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User


async def get_user_by_email(session: AsyncSession, email: str) -> Optional[User]:
    result = await session.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def create_user(session: AsyncSession, email: str, password: str) -> User:
    user = User(email=email, password_hash=bcrypt.hash(password))
    session.add(user)
    await session.flush()
    return user


async def verify_credentials(session: AsyncSession, email: str, password: str) -> Optional[User]:
    user = await get_user_by_email(session, email)
    if user and bcrypt.verify(password, user.password_hash):
        return user
    return None



