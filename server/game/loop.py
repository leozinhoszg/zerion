import asyncio
import time
from typing import Optional, Dict, Deque
from collections import deque
from .aoi import GridAoI, Entity
from .types import build_msg
from .state import WorldState, Player
from game import map_loader as map_module


class GameServer:
    """Loop autoritativo simples (tick rate configurável)."""

    def __init__(self, tick_hz: int = 10) -> None:
        self.tick_hz = tick_hz
        self._task: Optional[asyncio.Task] = None
        self._running = asyncio.Event()
        self._last_tick_ts: float | None = None
        self.aoi = GridAoI(cell_size=16)
        self.entities: Dict[str, Entity] = {}
        self.state_seq: int = 0
        # inputs por player: fila ordenada por seq e último seq aplicado
        self.player_inputs: Dict[str, Deque[dict]] = {}
        self.last_input_seq_applied: Dict[str, int] = {}
        self.world = WorldState()
        # rastreio de versão enviada por player
        self.sent_version_by_player: Dict[str, Dict[str, int]] = {}
        # células assinadas por player
        # self.subscriptions_by_player poderia ser usada se assinarmos células explicitamente

    def start(self) -> None:
        if self._task and not self._task.done():
            return
        self._running.set()
        self._task = asyncio.create_task(self._run_loop(), name="game_loop")

    async def stop(self) -> None:
        self._running.clear()
        if self._task:
            await self._task

    async def _run_loop(self) -> None:
        tick_interval = 1.0 / float(self.tick_hz)
        self._last_tick_ts = time.perf_counter()
        try:
            while self._running.is_set():
                now = time.perf_counter()
                dt = now - (self._last_tick_ts or now)
                self._last_tick_ts = now

                # TODO: sistemas de jogo (movimento, colisão, combate, regen, etc.)
                await self._tick(dt)

                # espera até o próximo tick, compensando drift simples
                elapsed = time.perf_counter() - now
                sleep_for = max(0.0, tick_interval - elapsed)
                await asyncio.sleep(sleep_for)
        except asyncio.CancelledError:
            pass

    async def _tick(self, dt: float) -> None:
        # incrementa seq global de estado a cada tick
        self.state_seq += 1
        _ = dt

    # API para WS: enfileirar input de movimento; retorna warn_code ou None
    def enqueue_move(self, player_id: str, msg: dict) -> str | None:
        # rate-limit simples por timestamp nos últimos 1s (feito no WS idealmente)
        # aqui apenas enfileira para processamento ordenado
        q = self.player_inputs.setdefault(player_id, deque())
        q.append(msg)
        return None

    # API para WS: aplicar inputs em ordem e retornar snapshot mínimo + ack
    def apply_inputs_and_build_state(self, player_id: str, you: Entity) -> dict:
        q = self.player_inputs.setdefault(player_id, deque())
        last_applied = self.last_input_seq_applied.get(player_id, 0)
        while q:
            m = q[0]
            seq = int(m.get("seq", 0))
            if seq <= last_applied:
                q.popleft()
                continue
            # ordem crescente: aplica o próximo
            q.popleft()
            dx = int(m.get("payload", {}).get("dx", 0))
            dy = int(m.get("payload", {}).get("dy", 0))
            if dx < -1 or dx > 1 or dy < -1 or dy > 1:
                continue
            # colisão autoritativa (slide por eixos)
            speed = 4
            nx = you.x + dx * speed
            ny = you.y
            mp = map_module.MAP
            if mp:
                # eixo X
                if not _is_aabb_blocked(mp, nx, ny):
                    you.x = nx
                # eixo Y
                nny = you.y + dy * speed
                if not _is_aabb_blocked(mp, you.x, nny):
                    you.y = nny
                # clamp bordas
                you.x = max(0, min(you.x, mp.width * mp.tile_w - 1))
                you.y = max(0, min(you.y, mp.height * mp.tile_h - 1))
            else:
                you.x = nx
                you.y = you.y + dy * speed
            last_applied = seq
        self.last_input_seq_applied[player_id] = last_applied
        # snapshot mínimo com seq global e ack do último input aplicado
        # calcular AoI e diffs
        # manter index de célula do próprio player (para AoI)
        self.aoi.set_entity_cell(you.id, you.x, you.y)
        visible_ids = list(self.aoi.visible_ids(you.x, you.y, radius=1))
        sent_version = self.sent_version_by_player.setdefault(player_id, {})
        payload = self.world.build_diffs(
            you=Player(id=you.id, x=you.x, y=you.y, hp=100, mp=50),
            visible_ids=visible_ids,
            sent_version=sent_version,
        )
        return build_msg(op="state", seq=self.state_seq, ack=last_applied, payload=payload)


def _is_aabb_blocked(mp, px: int, py: int) -> bool:
    # AABB do player: 20x20 px com ponto central (px,py)
    half = 10
    points = [
        (px - half, py - half),
        (px + half, py - half),
        (px - half, py + half),
        (px + half, py + half),
    ]
    for (x, y) in points:
        if not mp.in_bounds_px(x, y) or mp.is_solid_px(x, y):
            return True
    return False


