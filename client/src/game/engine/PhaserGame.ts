import Phaser from "phaser";

class BootScene extends Phaser.Scene {
  constructor() {
    super("boot");
  }
  preload() {}
  create() {
    this.scene.start("main");
  }
}

class MainScene extends Phaser.Scene {
  constructor() {
    super("main");
  }
  chatLines: string[] = [];
  chatText!: Phaser.GameObjects.Text;
  inputBuffer = "";

  player!: Phaser.GameObjects.Rectangle;
  tileW = 32;
  tileH = 32;
  shadow: any = null;
  create() {
    const w = this.scale.width;
    const h = this.scale.height;
    this.add.text(w / 2, 40, "Zerion", { color: "#ffffff" }).setOrigin(0.5);

    this.chatText = this.add
      .text(8, h - 150, "", {
        color: "#d1d5db",
        fontSize: "12px",
        fontFamily: "monospace",
      })
      .setOrigin(0, 0)
      .setDepth(10);

    // overlay do input atual na parte inferior
    const inputText = this.add
      .text(8, h - 20, "> ", {
        color: "#93c5fd",
        fontSize: "13px",
        fontFamily: "monospace",
      })
      .setOrigin(0, 0)
      .setDepth(10);

    // ouvir eventos de chat do servidor para overlay
    const remove = gameEvents.onChat((m) => {
      this.chatLines.push(`[${m.channel}] ${m.from}: ${m.msg}`);
      if (this.chatLines.length > 8) this.chatLines.shift();
      this.chatText.setText(this.chatLines.join("\n"));
    });
    this.events.once(Phaser.Scenes.Events.SHUTDOWN, () => remove());

    // captura de teclado simples dentro do canvas: Enter envia
    this.input.keyboard?.on("keydown", (ev: KeyboardEvent) => {
      if (ev.key === "Backspace") {
        this.inputBuffer = this.inputBuffer.slice(0, -1);
      } else if (ev.key.length === 1 && !ev.ctrlKey && !ev.metaKey) {
        this.inputBuffer += ev.key;
      } else if (ev.key === "Enter") {
        const text = this.inputBuffer.trim();
        if (text) gameEvents.emitClientChat(text);
        this.inputBuffer = "";
      }
      inputText.setText("> " + this.inputBuffer);
    });

    // marcador de player
    this.player = this.add
      .rectangle(w / 2, h / 2, 10, 10, 0x22c55e)
      .setOrigin(0.5);
    // placeholder: reagir a setas para enviar movimentos ao servidor
    this.input.keyboard?.on("keydown", (ev: KeyboardEvent) => {
      const sendMove = (dx: number, dy: number) =>
        gameEvents.emitClientMove(dx, dy);
      if (ev.key === "ArrowUp") sendMove(0, -1);
      if (ev.key === "ArrowDown") sendMove(0, 1);
      if (ev.key === "ArrowLeft") sendMove(-1, 0);
      if (ev.key === "ArrowRight") sendMove(1, 0);
    });

    // receber snapshots do servidor para atualizar player (no futuro: múltiplas entidades)
    const removeState = gameEvents.onServerState((state) => {
      const w2 = this.scale.width / 2;
      const h2 = this.scale.height / 2;
      this.player.setPosition(w2 + state.you.x, h2 + state.you.y);
    });
    this.events.once(Phaser.Scenes.Events.SHUTDOWN, () => removeState());
  }
}

import { gameEvents } from "@/game/events";
export function createPhaserGame(parent: HTMLElement): Phaser.Game {
  return new Phaser.Game({
    type: Phaser.AUTO,
    parent,
    width: 800,
    height: 600,
    backgroundColor: "#0f172a",
    physics: { default: "arcade", arcade: { debug: false } },
    scene: [BootScene, MainScene],
  });
}
