export type Op =
  | "hello"
  | "ping"
  | "move"
  | "chat"
  | "state"
  | "event"
  | "warn"
  | "resync";
export type Msg<T = unknown> = {
  v: 1;
  op: Op;
  seq?: number;
  ack?: number;
  ts: number;
  payload?: T;
};

export type HelloPayload = { tick_hz: number; server_time_ms: number };
export type MovePayload = { dx: number; dy: number };
export type ChatPayload = { channel: string; msg: string };
export type EventPayload = {
  channel?: string;
  from?: string;
  msg?: string;
  ts?: number;
  code?: string;
};
export type StatePayload = {
  you: { x: number; y: number; hp: number; mp: number };
  entities: Array<{ id: string; x: number; y: number; kind: string }>;
};
