from __future__ import annotations

import json
import hashlib
import os
from typing import List, Tuple


class MapData:
    def __init__(
        self,
        id: str,
        version: str,
        width: int,
        height: int,
        tile_w: int,
        tile_h: int,
        solids: List[List[bool]],
        spawn: Tuple[int, int] = (0, 0),
    ) -> None:
        self.id = id
        self.version = version
        self.width = width
        self.height = height
        self.tile_w = tile_w
        self.tile_h = tile_h
        self.solids = solids  # [y][x] bool
        self.spawn = spawn

    def in_bounds_px(self, px: int, py: int) -> bool:
        return 0 <= px < self.width * self.tile_w and 0 <= py < self.height * self.tile_h

    def is_solid_tile(self, tx: int, ty: int) -> bool:
        if tx < 0 or ty < 0 or tx >= self.width or ty >= self.height:
            return True
        return self.solids[ty][tx]

    def is_solid_px(self, px: int, py: int) -> bool:
        return self.is_solid_tile(px // self.tile_w, py // self.tile_h)


def load_tiled_json(path: str, map_id: str) -> MapData:
    with open(path, "r", encoding="utf-8") as f:
        raw = f.read()
    data = json.loads(raw)
    version = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:8]
    w, h = int(data["width"]), int(data["height"])
    tw, th = int(data["tilewidth"]), int(data["tileheight"])
    solids: List[List[bool]] = [[False for _ in range(w)] for _ in range(h)]

    # layer com property collision: true
    layers = data.get("layers", [])
    coll_layers = [
        ly
        for ly in layers
        if ly.get("type") == "tilelayer"
        and any(p.get("name") == "collision" and p.get("value") is True for p in ly.get("properties", []) or [])
    ]

    # tiles com property solid: true
    gid_solid = set()
    for ts in data.get("tilesets", []) or []:
        tiles = ts.get("tiles", []) or []
        for t in tiles:
            props = t.get("properties", []) or []
            if any(p.get("name") == "solid" and p.get("value") is True for p in props):
                firstgid = int(ts.get("firstgid", 1))
                gid_solid.add(firstgid + int(t["id"]))

    if coll_layers:
        for ly in coll_layers:
            gid = ly["data"]
            for i, g in enumerate(gid):
                if g and g != 0:
                    x = i % w
                    y = i // w
                    solids[y][x] = True
    elif gid_solid:
        for ly in [ly for ly in layers if ly.get("type") == "tilelayer"]:
            gid = ly["data"]
            for i, g in enumerate(gid):
                if g in gid_solid:
                    x = i % w
                    y = i // w
                    solids[y][x] = True

    spawn = (0, 0)
    for ly in layers:
        if ly.get("type") == "objectgroup" and ly.get("name") == "spawns":
            for obj in ly.get("objects", []) or []:
                if obj.get("name") == "player_spawn":
                    spawn = (int(obj.get("x", 0)), int(obj.get("y", 0)))

    return MapData(map_id, version, w, h, tw, th, solids, spawn)


# Global opcional (preenchido no boot)
MAP: MapData | None = None



