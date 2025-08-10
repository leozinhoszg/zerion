from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict, List, Tuple, Any

from .aoi import Entity


@dataclass
class Player:
    id: str
    x: int
    y: int
    hp: int = 100
    mp: int = 50


class WorldState:
    def __init__(self) -> None:
        self.entities: Dict[str, Entity] = {}
        self.entity_version: Dict[str, int] = {}

    def upsert_entity(self, e: Entity) -> None:
        exists = e.id in self.entities
        self.entities[e.id] = e
        self.entity_version[e.id] = self.entity_version.get(e.id, 0) + 1

    def remove_entity(self, entity_id: str) -> None:
        self.entities.pop(entity_id, None)
        self.entity_version.pop(entity_id, None)

    def build_diffs(self, you: Player, visible_ids: List[str], sent_version: Dict[str, int]) -> Dict[str, Any]:
        added: List[Dict[str, Any]] = []
        updated: List[Dict[str, Any]] = []
        removed: List[str] = []

        visible_set = set(visible_ids)
        # removidos: tudo que eu enviei antes mas não está mais visível ou foi removido
        for eid in list(sent_version.keys()):
            if eid not in visible_set or eid not in self.entities:
                removed.append(eid)
                sent_version.pop(eid, None)

        # added/updated
        for eid in visible_ids:
            ent = self.entities.get(eid)
            if not ent:
                continue
            ver = self.entity_version.get(eid, 0)
            sent_ver = sent_version.get(eid)
            if sent_ver is None:
                added.append({
                    "id": ent.id,
                    "kind": ent.kind,
                    "x": ent.x,
                    "y": ent.y,
                    "hp": ent.hp,
                    "meta": ent.meta or {},
                })
                sent_version[eid] = ver
            elif ver > sent_ver:
                # montar patch com apenas campos alterados
                patch: Dict[str, Any] = {}
                # Para simplicidade, consideramos possíveis campos a cada versão
                patch["x"] = ent.x
                patch["y"] = ent.y
                patch["hp"] = ent.hp
                if ent.meta is not None:
                    patch["meta"] = ent.meta
                updated.append({"id": eid, "patch": patch})
                sent_version[eid] = ver

        return {
            "you": {"x": you.x, "y": you.y, "hp": you.hp, "mp": you.mp},
            "added": added,
            "updated": updated,
            "removed": removed,
        }




