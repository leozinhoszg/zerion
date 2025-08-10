from __future__ import annotations

from typing import Any, Literal, TypedDict
import time


Op = Literal["hello", "ping", "move", "chat", "state", "event", "warn", "resync"]


class Msg(TypedDict, total=False):
    v: int
    op: Op
    seq: int
    ack: int
    ts: int
    payload: dict[str, Any] | list[Any] | str | int | float | None


ALLOWED_OPS: set[str] = {
    "hello",
    "ping",
    "move",
    "chat",
    "state",
    "event",
    "warn",
    "resync",
}


def now_ms() -> int:
    return int(time.time() * 1000)


def build_msg(op: Op, payload: Any | None = None, seq: int | None = None, ack: int | None = None) -> Msg:
    msg: Msg = {"v": 1, "op": op, "ts": now_ms()}
    if seq is not None:
        msg["seq"] = int(seq)
    if ack is not None:
        msg["ack"] = int(ack)
    if payload is not None:
        msg["payload"] = payload  # type: ignore[assignment]
    return msg


def parse_msg(raw: Any) -> Msg | None:
    if not isinstance(raw, dict):
        return None
    v = raw.get("v")
    op = raw.get("op")
    if v != 1 or not isinstance(op, str) or op not in ALLOWED_OPS:
        return None
    # seq/ack/ts opcionais, mas quando presentes devem ser ints
    for k in ("seq", "ack", "ts"):
        if k in raw and not isinstance(raw[k], int):
            return None
    return raw  # type: ignore[return-value]




