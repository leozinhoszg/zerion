from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict, List, Set, Tuple, Any, Optional, Iterable


ChunkCoord = Tuple[int, int]
CELL_SIZE = 16


@dataclass
class Entity:
  id: str
  kind: str
  x: int
  y: int
  hp: int = 100
  meta: Optional[Dict[str, Any]] = None


class GridAoI:
  """Grade espacial simples baseada em chunks quadrados.

  - cell_size: tamanho do chunk em tiles/pixels
  - mantém mapeamento bidirecional: entidade -> chunk e chunk -> set de entidades
  """

  def __init__(self, cell_size: int = 16):
    self.cell_size = cell_size
    self.chunk_to_entities: Dict[ChunkCoord, Set[str]] = {}
    self.entity_to_chunk: Dict[str, ChunkCoord] = {}

  def _to_chunk(self, x: int, y: int) -> ChunkCoord:
    return (x // self.cell_size, y // self.cell_size)

  def pos_to_cell(self, x: int, y: int) -> ChunkCoord:
    return self._to_chunk(x, y)

  def add_or_move(self, ent: Entity) -> None:
    new_chunk = self._to_chunk(ent.x, ent.y)
    old_chunk = self.entity_to_chunk.get(ent.id)
    if old_chunk == new_chunk:
      return
    if old_chunk:
      s = self.chunk_to_entities.get(old_chunk)
      if s:
        s.discard(ent.id)
        if not s:
          self.chunk_to_entities.pop(old_chunk, None)
    self.entity_to_chunk[ent.id] = new_chunk
    self.chunk_to_entities.setdefault(new_chunk, set()).add(ent.id)

  def set_entity_cell(self, entity_id: str, x: int, y: int) -> None:
    new_chunk = self._to_chunk(x, y)
    old_chunk = self.entity_to_chunk.get(entity_id)
    if old_chunk == new_chunk:
      return
    if old_chunk:
      s = self.chunk_to_entities.get(old_chunk)
      if s:
        s.discard(entity_id)
        if not s:
          self.chunk_to_entities.pop(old_chunk, None)
    self.entity_to_chunk[entity_id] = new_chunk
    self.chunk_to_entities.setdefault(new_chunk, set()).add(entity_id)

  def remove(self, entity_id: str) -> None:
    chunk = self.entity_to_chunk.pop(entity_id, None)
    if not chunk:
      return
    s = self.chunk_to_entities.get(chunk)
    if s:
      s.discard(entity_id)
      if not s:
        self.chunk_to_entities.pop(chunk, None)

  def neighbors(self, x: int, y: int, radius_chunks: int = 1) -> Set[str]:
    cx, cy = self._to_chunk(x, y)
    out: Set[str] = set()
    for dx in range(-radius_chunks, radius_chunks + 1):
      for dy in range(-radius_chunks, radius_chunks + 1):
        s = self.chunk_to_entities.get((cx + dx, cy + dy))
        if s:
          out.update(s)
    return out

  def neighbor_cells(self, x: int, y: int, radius_chunks: int = 1) -> Set[ChunkCoord]:
    cx, cy = self._to_chunk(x, y)
    cells: Set[ChunkCoord] = set()
    for dx in range(-radius_chunks, radius_chunks + 1):
      for dy in range(-radius_chunks, radius_chunks + 1):
        cells.add((cx + dx, cy + dy))
    return cells

  def neighbors_of_cell(self, cx: int, cy: int, radius: int = 1) -> Iterable[ChunkCoord]:
    for dx in range(-radius, radius + 1):
      for dy in range(-radius, radius + 1):
        yield (cx + dx, cy + dy)

  def visible_ids(self, x: int, y: int, radius: int = 1) -> Set[str]:
    cx, cy = self._to_chunk(x, y)
    vis: Set[str] = set()
    for nc in self.neighbors_of_cell(cx, cy, radius):
      vis |= self.chunk_to_entities.get(nc, set())
    return vis




