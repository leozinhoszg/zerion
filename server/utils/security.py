from __future__ import annotations

from fastapi import WebSocket
from app.config import get_settings


def is_origin_allowed(origin: str | None) -> bool:
    if not origin:
        return False
    settings = get_settings()
    return origin in settings.allowed_ws_origins


def extract_subprotocols(headers: dict[str, str]) -> list[str]:
    value = headers.get("sec-websocket-protocol") or headers.get("Sec-WebSocket-Protocol")
    if not value:
        return []
    # protocolo múltiplo separado por vírgula
    return [p.strip() for p in value.split(",") if p.strip()]




