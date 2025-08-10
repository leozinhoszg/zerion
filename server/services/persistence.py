from __future__ import annotations

import asyncio
from typing import Dict, Optional

from services.db import AsyncSessionLocal
from services.repositories.character_repository import update_state_by_id


class PersistenceManager:
    def __init__(self, interval_seconds: int = 5) -> None:
        self.interval_seconds = interval_seconds
        self._task: Optional[asyncio.Task] = None
        self._running = asyncio.Event()
        self._dirty: Dict[int, dict] = {}

    def mark_dirty(self, char_id: int, *, x: int, y: int, hp: int, mp: int) -> None:
        self._dirty[char_id] = {"x": x, "y": y, "hp": hp, "mp": mp}

    async def start(self) -> None:
        if self._task and not self._task.done():
            return
        self._running.set()
        self._task = asyncio.create_task(self._run_loop(), name="persistence_loop")

    async def stop(self) -> None:
        self._running.clear()
        if self._task:
            await self._task

    async def flush_now(self, only_char_id: Optional[int] = None) -> None:
        payloads = self._dirty.copy()
        if only_char_id is not None:
            payloads = {k: v for k, v in payloads.items() if k == only_char_id}
        if not payloads:
            return
        async with AsyncSessionLocal() as session:
            for char_id, data in payloads.items():
                await update_state_by_id(session, char_id, **data)
            await session.commit()
        # limpar somente os que foram flushados
        for k in list(payloads.keys()):
            self._dirty.pop(k, None)

    async def _run_loop(self) -> None:
        try:
            while self._running.is_set():
                await asyncio.sleep(self.interval_seconds)
                await self.flush_now()
        except asyncio.CancelledError:
            pass


persistence_manager = PersistenceManager(interval_seconds=5)



