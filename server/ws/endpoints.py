from typing import Optional, Any

import asyncio
import contextlib
import time
import umsgpack
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from services.redis import redis_manager, pop_ws_ticket
from services.db import get_db
from services.repositories.character_repository import get_by_user, create_default
from services.persistence import persistence_manager
from game.state import Player
from game.loop import GameServer
from game.types import parse_msg, build_msg, now_ms
from game import map_loader as map_module
from app.config import get_settings
from utils.security import is_origin_allowed, extract_subprotocols
from utils.ratelimit import allow, allow_per_second


router = APIRouter()
active_sockets: set[WebSocket] = set()


@router.websocket("/ws")
async def ws_endpoint(websocket: WebSocket):
    settings = get_settings()
    origin = websocket.headers.get("origin")
    if not is_origin_allowed(origin):
        await websocket.close(code=1008)
        return

    subprotocols = extract_subprotocols(dict(websocket.headers))
    if "zerion.v1" not in subprotocols:
        await websocket.close(code=1008)
        return
    ticket_proto = next((p for p in subprotocols if p.startswith("auth.")), None)
    if not ticket_proto or len(ticket_proto) <= 5:
        await websocket.close(code=1008)
        return
    ticket = ticket_proto.split(".", 1)[1]
    user_id_int = await pop_ws_ticket(ticket)
    if user_id_int is None:
        await websocket.close(code=1008)
        return
    user_id = str(user_id_int)

    await websocket.accept(subprotocol="zerion.v1")
    active_sockets.add(websocket)

    # Redis pub/sub para chat global
    redis = None
    pubsub = None
    try:
        redis = await redis_manager.get_client()
        pubsub = redis.pubsub()
        await pubsub.subscribe("chat:global")
    except Exception:
        redis = None
        pubsub = None

    async def forward_pubsub():
        async for message in pubsub.listen():
            if message.get("type") != "message":
                continue
            payload = umsgpack.unpackb(message["data"])  # publish como msgpack
            data = umsgpack.packb({"t": "event", "type": "msg", "payload": {"channel": "global", **payload}})
            await websocket.send_bytes(data)

    forward_task = asyncio.create_task(forward_pubsub()) if pubsub else None
    # Carregar/crear personagem real do DB
    char_id: int | None = None
    async with get_db() as session:
        char = await get_by_user(session, int(user_id))
        if not char:
            char = await create_default(session, int(user_id))
        char_id = int(char.id)
        await session.commit()
        you = Player(id=user_id, x=int(char.x), y=int(char.y))
    # iniciar loop de persistência se ainda não
    await persistence_manager.start()
    last_client_seq = 0
    move_rate_key = f"rl:move:{user_id}"
    server = GameServer(tick_hz=settings and getattr(settings, 'tick_hz', 10) or 10)

    # hello inicial
    map_info = None
    if map_module.MAP:
        map_info = {"id": map_module.MAP.id, "version": map_module.MAP.version, "tile_w": map_module.MAP.tile_w, "tile_h": map_module.MAP.tile_h}
    hello = build_msg("hello", {"tick_hz": server.tick_hz, "server_time_ms": now_ms(), "map": map_info})
    await websocket.send_bytes(umsgpack.packb(hello))

    try:
        while True:
            raw = await websocket.receive_bytes()
            decoded = umsgpack.unpackb(raw)
            msg = parse_msg(decoded)
            if not msg:
                continue
            op = msg.get("op")
            seq = int(msg.get("seq", 0))
            if seq and seq <= last_client_seq:
                # fora de ordem/repetido
                continue
            if seq:
                last_client_seq = seq
            if op == "ping":
                out = build_msg("ping")
                await websocket.send_bytes(umsgpack.packb(out))
            elif op == "chat":
                payload_in = (msg.get("payload") or {})  # type: ignore[assignment]
                channel = payload_in.get("channel", "global")
                msg_text = str(payload_in.get("msg", ""))[:200]
                # publica no canal (apenas global por enquanto)
                if channel != "global":
                    continue
                # rate-limit por usuário
                if not await allow(f"rl:chat:{user_id}", settings.rate_chat_max):
                    warn = umsgpack.packb({"t": "event", "type": "warn", "payload": {"code": "chat_rate_limited"}})
                    await websocket.send_bytes(warn)
                    continue
                payload = {"from": user_id, "msg": msg_text, "ts": int(time.time() * 1000)}
                if redis:
                    await redis.publish("chat:global", umsgpack.packb(payload))
                else:
                    event = umsgpack.packb({"t": "event", "type": "msg", "payload": {"channel": "global", **payload}})
                    # broadcast local
                    for ws in list(active_sockets):
                        try:
                            await ws.send_bytes(event)
                        except Exception:
                            pass
            elif op == "move":
                # rate-limit por segundo no server também
                if not await allow_per_second(move_rate_key, 20):
                    warn = build_msg("warn", {"code": "rate_move"})
                    await websocket.send_bytes(umsgpack.packb(warn))
                    continue
                server.enqueue_move(user_id, msg)
                snap = server.apply_inputs_and_build_state(user_id, you)
                # marca dirty para flush periódico
                if char_id is not None:
                    persistence_manager.mark_dirty(char_id, x=you.x, y=you.y, hp=100, mp=50)
                await websocket.send_bytes(umsgpack.packb(snap))
            # outros tipos (move, cast, etc.) serão tratados no loop do jogo
    except WebSocketDisconnect:
        pass
    finally:
        if forward_task:
            forward_task.cancel()
        with contextlib.suppress(Exception):
            if pubsub:
                await pubsub.unsubscribe("chat:global")
                await pubsub.close()
        with contextlib.suppress(Exception):
            active_sockets.discard(websocket)
        # flush final do personagem
        with contextlib.suppress(Exception):
            if char_id is not None:
                await persistence_manager.flush_now(only_char_id=char_id)


