from __future__ import annotations

from typing import Optional

from redis.asyncio import Redis

from app.config import get_settings
import os
import secrets


class RedisManager:
    def __init__(self) -> None:
        self._client: Optional[Redis] = None

    async def get_client(self) -> Redis:
        if not self._client:
            settings = get_settings()
            # Mantemos binário para poder enviar/receber msgpack diretamente
            self._client = Redis.from_url(settings.redis_url, decode_responses=False)
        return self._client

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()


# Singleton simples para reutilizar conexões
redis_manager = RedisManager()


async def issue_ws_ticket(user_id: int, ttl: int | None = None) -> str:
    settings = get_settings()
    ttl = ttl or settings.ticket_ttl_seconds
    ticket = secrets.token_urlsafe(24)
    key = f"ws:ticket:{ticket}"
    client = await redis_manager.get_client()
    # valor salvo como user_id
    await client.set(key, str(user_id), ex=ttl)
    return ticket


async def pop_ws_ticket(ticket: str) -> int | None:
    client = await redis_manager.get_client()
    key = f"ws:ticket:{ticket}"
    # GETDEL consome o ticket (Redis >= 6.2); se indisponível, use lua/tx
    try:
        raw = await client.execute_command("GETDEL", key)
    except Exception:
        # fallback: GET e DEL (não ótimo, mas suficiente para MVP)
        raw = await client.get(key)
        if raw is not None:
            await client.delete(key)
    if raw is None:
        return None
    try:
        return int(raw.decode() if isinstance(raw, (bytes, bytearray)) else raw)
    except Exception:
        return None


