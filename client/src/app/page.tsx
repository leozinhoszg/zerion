"use client";
import dynamic from "next/dynamic";
const GameCanvas = dynamic(() => import("@/game/components/GameCanvas"), {
  ssr: false,
});
import { useGameStore } from "@/store/useGameStore";
import Chat from "@/ui/Chat";

export default function HomePage() {
  const connected = useGameStore((s) => s.connected);
  const connect = useGameStore((s) => s.connect);
  const disconnect = useGameStore((s) => s.disconnect);
  const ping = useGameStore((s) => s.ping);
  const lastPong = useGameStore((s) => s.lastPongTs);

  return (
    <main className="flex min-h-screen flex-col items-center gap-6 py-8">
      <h1 className="text-3xl font-bold">Zerion</h1>
      <div className="flex gap-3">
        {!connected ? (
          <button
            onClick={connect}
            className="rounded bg-emerald-600 px-3 py-1"
          >
            Conectar
          </button>
        ) : (
          <>
            <button onClick={ping} className="rounded bg-sky-600 px-3 py-1">
              Ping
            </button>
            <button
              onClick={disconnect}
              className="rounded bg-rose-600 px-3 py-1"
            >
              Desconectar
            </button>
          </>
        )}
      </div>
      <p className="text-slate-300">
        Last pong: {lastPong ? new Date(lastPong).toLocaleTimeString() : "-"}
      </p>
      <GameCanvas />
      <Chat />
    </main>
  );
}
