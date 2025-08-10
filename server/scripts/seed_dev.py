from __future__ import annotations

import asyncio

from services.db import AsyncSessionLocal
from services.repositories.user_repository import get_user_by_email, create_user
from services.repositories.character_repository import get_by_user, create_default


async def main() -> None:
    async with AsyncSessionLocal() as session:
        user = await get_user_by_email(session, "demo@zerion.local")
        if not user:
            user = await create_user(session, "demo@zerion.local", "demo")
        char = await get_by_user(session, int(user.id))
        if not char:
            await create_default(session, int(user.id))
        await session.commit()
    print("Seed concluído: demo@zerion.local / demo")


if __name__ == "__main__":
    asyncio.run(main())



