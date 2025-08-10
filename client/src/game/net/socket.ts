import { encode, decode } from "@msgpack/msgpack";
import type { Msg, MovePayload, StatePayload, EventPayload } from "./protocol";
import { ClientWorldState } from "@/game/state";
import { gameEvents } from "@/game/events";

type Listener = (msg: any) => void;

export class ZerionSocket {
  private ws: WebSocket | null = null;
  private listeners = new Set<Listener>();
  private backoffMs = 1000;
  private maxBackoffMs = 15000;
  private shouldReconnect = false;
  private token: string | null = null;
  private seqCounter = 0;
  private pendingInputs = new Map<
    number,
    { dx: number; dy: number; ts: number }
  >();
  private lastAck = 0;
  private world = new ClientWorldState();

  addListener(cb: Listener) {
    this.listeners.add(cb);
    return () => this.listeners.delete(cb);
  }

  async connect(token: string): Promise<void> {
    this.token = token;
    const base = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000/ws";
    const protocols = ["zerion.v1", "auth." + (await getWSTicket(token))];
    this.ws = new WebSocket(base, protocols);
    this.shouldReconnect = true;
    await new Promise<void>((resolve, reject) => {
      if (!this.ws) return reject(new Error("ws null"));
      this.ws.binaryType = "arraybuffer";
      this.ws.onopen = () => resolve();
      this.ws.onerror = (ev) => reject(ev as any);
      this.ws.onmessage = (ev: MessageEvent<ArrayBuffer | string>) =>
        this.onMessage(ev);
      this.ws.onclose = () => {
        if (this.shouldReconnect) this.scheduleReconnect();
      };
    });
  }

  private onMessage(ev: MessageEvent<ArrayBuffer | string>) {
    try {
      const buf =
        typeof ev.data === "string"
          ? new TextEncoder().encode(ev.data)
          : new Uint8Array(ev.data as ArrayBuffer);
      const msg = decode(buf) as Msg<any>;
      if (msg.op === "hello") {
        gameEvents.emitHello(msg.payload || {});
        return;
      }
      if (msg.op === "state") {
        if (msg.ack && msg.ack > this.lastAck) this.lastAck = msg.ack;
        for (const k of Array.from(this.pendingInputs.keys()))
          if (k <= (msg.ack ?? 0)) this.pendingInputs.delete(k);
        const state = msg.payload as StatePayload;
        let x = state.you.x;
        let y = state.you.y;
        // AoI diffs
        const p: any = state as any;
        if (p.added || p.updated || p.removed) {
          if (p.added) this.world.applyAdded(p.added);
          if (p.updated) this.world.applyUpdated(p.updated);
          if (p.removed) this.world.applyRemoved(p.removed);
        }
        for (const [seq, input] of Array.from(
          this.pendingInputs.entries()
        ).sort((a, b) => a[0] - b[0])) {
          x += input.dx;
          y += input.dy;
        }
        gameEvents.emitServerState({
          you: { ...state.you, x, y },
          entities: state.entities,
        } as any);
        return;
      }
      if (msg.op === "event") {
        const e = msg.payload as EventPayload;
        if (e && (e as any).channel)
          gameEvents.emitChat({
            channel: e.channel!,
            from: e.from!,
            msg: e.msg!,
            ts: e.ts!,
          });
        return;
      }
    } catch {
      // ignore
    }
  }

  sendMove(dx: number, dy: number) {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) return;
    const seq = ++this.seqCounter;
    const ts = Date.now();
    this.pendingInputs.set(seq, { dx, dy, ts });
    const msg: Msg<MovePayload> = {
      v: 1,
      op: "move",
      seq,
      ts,
      payload: { dx, dy },
    };
    this.ws.send(encode(msg));
  }

  sendPing() {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) return;
    const msg: Msg = { v: 1, op: "ping", ts: Date.now() };
    this.ws.send(encode(msg));
  }

  sendChat(channel: string, text: string) {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) return;
    const msg: Msg<{ channel: string; msg: string }> = {
      v: 1,
      op: "chat",
      ts: Date.now(),
      payload: { channel, msg: text },
    };
    this.ws.send(encode(msg));
  }

  close() {
    this.shouldReconnect = false;
    this.ws?.close();
    this.ws = null;
  }

  private async scheduleReconnect() {
    const delay = this.backoffMs;
    await new Promise((r) => setTimeout(r, delay));
    this.backoffMs = Math.min(this.backoffMs * 2, this.maxBackoffMs);
    if (!this.token) return;
    try {
      await this.connect(this.token);
      this.backoffMs = 1000;
    } catch {
      this.scheduleReconnect();
    }
  }
}
async function getWSTicket(accessToken: string): Promise<string> {
  const api = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";
  const res = await fetch(`${api}/auth/ticket`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
  if (!res.ok) throw new Error("ticket falhou");
  const data = (await res.json()) as { ticket: string };
  return data.ticket;
}
