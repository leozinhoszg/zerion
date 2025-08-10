import { create } from "zustand";
import { ZerionSocket } from "@/game/net/socket";
import type { ServerMessage } from "@/game/net/protocol";
import { gameEvents } from "@/game/events";

type GameState = {
  token: string | null;
  connected: boolean;
  lastPongTs: number | null;
  chatInput: string;
  chatLog: Array<{ channel: string; from: string; msg: string; ts: number }>;
  connect: () => Promise<void>;
  disconnect: () => void;
  ping: () => void;
  sendChat: () => void;
  setChatInput: (v: string) => void;
};

export const useGameStore = create<GameState>((set, get) => {
  const socket = new ZerionSocket();

  const onMessage = (_msg: any) => {};

  return {
    token: null,
    connected: false,
    lastPongTs: null,
    chatInput: "",
    chatLog: [],
    connect: async () => {
      // login dev
      const api = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";
      const res = await fetch(`${api}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: "demo@zerion.local", password: "demo" }),
      });
      if (!res.ok) throw new Error("login falhou");
      const { access_token } = await res.json();
      await socket.connect(access_token);
      // socket.addListener(onMessage);  // listener antigo (protocolo v0) desativado
      set({ token: access_token, connected: true });
      // Escuta de chat emitido no canvas (Enter)
      gameEvents.onClientChat((text) => {
        socket.sendChat?.("global", text);
      });
      gameEvents.onClientMove((dx, dy) => {
        socket.sendMove?.(dx, dy);
      });
    },
    disconnect: () => {
      socket.close();
      set({ connected: false });
    },
    ping: () => {
      socket.sendPing?.();
    },
    sendChat: () => {
      const text = get().chatInput.trim();
      if (!text) return;
      socket.sendChat?.("global", text);
      set({ chatInput: "" });
    },
    // duplicado antigo removido
    setChatInput: (v: string) => set({ chatInput: v }),
  };
});
