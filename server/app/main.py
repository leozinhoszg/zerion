from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
import os
from game.map_loader import load_tiled_json
from game import map_loader as map_module
from routes.health import router as health_router
from routes.auth import router as auth_router
from ws.endpoints import router as ws_router
from game.loop import GameServer
from game.state import Player
from services.redis import redis_manager
from services.persistence import persistence_manager


settings = get_settings()
game_server = GameServer(tick_hz=10)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    # Carrega mapa Tiled
    try:
        base = os.path.dirname(__file__)
        map_path = os.path.normpath(os.path.join(base, "../assets/maps/zerion_start.json"))
        map_module.MAP = load_tiled_json(map_path, "zerion_start")
    except Exception:
        map_module.MAP = None
    game_server.start()
    await persistence_manager.start()
    # Inicializa Redis cedo
    try:
        await redis_manager.get_client()
    except Exception:
        pass
    try:
        yield
    finally:
        # Shutdown
        await game_server.stop()
        await persistence_manager.stop()
        await redis_manager.close()


app = FastAPI(lifespan=lifespan, title="Zerion API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(ws_router)


@app.get("/")
async def root():
    return {"name": "Zerion API", "status": "ok"}


