from __future__ import annotations

import time
from typing import Optional

from services.redis import redis_manager


async def allow(key: str, max_per_minute: int) -> bool:
    """Token bucket simples em Redis com janela deslizante de 60s.

    Implementação MVP: usa INCR e EXPIRE com TTL 60s.
    """
    client = await redis_manager.get_client()
    now = int(time.time())
    window_key = f"{key}:{now // 60}"
    current = await client.incr(window_key)
    if current == 1:
        await client.expire(window_key, 60)
    return current <= max_per_minute


async def allow_per_second(key: str, max_per_second: int) -> bool:
    """Janela de 1 segundo usando INCR + EXPIRE(2s)."""
    client = await redis_manager.get_client()
    now = int(time.time())
    k = f"{key}:{now}"
    current = await client.incr(k)
    if current == 1:
        await client.expire(k, 2)
    return current <= max_per_second


