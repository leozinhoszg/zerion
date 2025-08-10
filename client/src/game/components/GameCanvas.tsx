"use client";
import { useEffect, useRef } from "react";
import { createPhaserGame } from "@/game/engine/PhaserGame";

export default function GameCanvas() {
  const containerRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;
    const game = createPhaserGame(containerRef.current);
    return () => {
      game.destroy(true);
    };
  }, []);

  return <div ref={containerRef} className="w-[800px] h-[600px] mx-auto" />;
}
