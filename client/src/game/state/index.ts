export type Entity = {
  id: string;
  kind: string;
  x: number;
  y: number;
  hp: number;
  meta?: Record<string, any>;
};

export class ClientWorldState {
  entities = new Map<string, Entity>();

  applyAdded(list: Entity[]) {
    for (const e of list) this.entities.set(e.id, e);
  }

  applyUpdated(list: Array<{ id: string; patch: Partial<Entity> }>) {
    for (const u of list) {
      const cur = this.entities.get(u.id);
      if (!cur) continue;
      Object.assign(cur, u.patch);
    }
  }

  applyRemoved(ids: string[]) {
    for (const id of ids) this.entities.delete(id);
  }
}

