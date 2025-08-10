export type ChatPayload = {
  channel: string;
  from: string;
  msg: string;
  ts: number;
};

const target = new EventTarget();

export const gameEvents = {
  onHello(
    listener: (payload: {
      map?: { id: string; version: string; tile_w: number; tile_h: number };
      mismatch?: boolean;
    }) => void
  ) {
    const handler = (e: Event) => listener((e as CustomEvent<any>).detail);
    target.addEventListener("server:hello", handler);
    return () => target.removeEventListener("server:hello", handler);
  },
  emitHello(payload: any) {
    target.dispatchEvent(new CustomEvent("server:hello", { detail: payload }));
  },
  onServerState(
    listener: (state: {
      you: { x: number; y: number; hp: number; mp: number };
    }) => void
  ) {
    const handler = (e: Event) => listener((e as CustomEvent<any>).detail);
    target.addEventListener("server:state", handler);
    return () => target.removeEventListener("server:state", handler);
  },
  emitServerState(state: any) {
    target.dispatchEvent(new CustomEvent("server:state", { detail: state }));
  },
  onChat(listener: (payload: ChatPayload) => void) {
    const handler = (e: Event) =>
      listener((e as CustomEvent<ChatPayload>).detail);
    target.addEventListener("server:chat", handler);
    return () => target.removeEventListener("server:chat", handler);
  },
  emitChat(payload: ChatPayload) {
    target.dispatchEvent(
      new CustomEvent<ChatPayload>("server:chat", { detail: payload })
    );
  },
  onClientChat(listener: (text: string) => void) {
    const handler = (e: Event) => listener((e as CustomEvent<string>).detail);
    target.addEventListener("client:chat", handler);
    return () => target.removeEventListener("client:chat", handler);
  },
  emitClientChat(text: string) {
    target.dispatchEvent(
      new CustomEvent<string>("client:chat", { detail: text })
    );
  },
  onClientMove(listener: (dx: number, dy: number) => void) {
    const handler = (e: Event) => {
      const [dx, dy] = (e as CustomEvent<[number, number]>).detail;
      listener(dx, dy);
    };
    target.addEventListener("client:move", handler);
    return () => target.removeEventListener("client:move", handler);
  },
  emitClientMove(dx: number, dy: number) {
    target.dispatchEvent(
      new CustomEvent<[number, number]>("client:move", { detail: [dx, dy] })
    );
  },
};
