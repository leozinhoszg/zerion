"use client";
import { useGameStore } from "@/store/useGameStore";

export default function Chat() {
  const connected = useGameStore((s) => s.connected);
  const chatInput = useGameStore((s) => s.chatInput);
  const setChatInput = useGameStore((s) => s.setChatInput);
  const sendChat = useGameStore((s) => s.sendChat);
  const chatLog = useGameStore((s) => s.chatLog);

  return (
    <div className="w-[800px] mx-auto border border-slate-700 rounded p-3">
      <div className="h-40 overflow-auto space-y-1 text-sm">
        {chatLog.map((m, idx) => (
          <div key={idx} className="text-slate-200">
            <span className="text-slate-400">[{m.channel}]</span>{" "}
            <b>{m.from}</b>: {m.msg}
          </div>
        ))}
      </div>
      <div className="mt-2 flex gap-2">
        <input
          value={chatInput}
          onChange={(e) => setChatInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") sendChat();
          }}
          placeholder={
            connected ? "Digite mensagem global..." : "Conecte-se para enviar"
          }
          disabled={!connected}
          className="flex-1 rounded bg-slate-800 px-2 py-1 outline-none"
        />
        <button
          onClick={sendChat}
          disabled={!connected}
          className="rounded bg-emerald-600 px-3 py-1"
        >
          Enviar
        </button>
      </div>
    </div>
  );
}



