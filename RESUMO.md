## Zerion — Resumo do que foi implementado (MVP inicial)

Este documento resume tudo que foi criado até aqui com base no plano em `projeto zerion.md`.

### Entregas principais

- Monorepo com `server` (FastAPI/WS) e `client` (Next 15 + TS + Tailwind + Phaser + Zustand)
- Docker Compose com `mysql`, `redis`, `server`, `client` e `nginx` (proxy com suporte a WS)
- Backend funcional: healthcheck, login dev (JWT), emissão e consumo de ticket curto para WS (Redis), validação de Origin e subprotocol, chat global com rate-limit, ping/pong, snapshots mínimos de estado em `move`
- Frontend funcional: página Next com canvas Phaser, overlay de chat (HUD), conexão WS binária com msgpack, Zustand para estado e ações (connect, ping, chat)

### Estrutura do projeto (arquivos/pastas criados)

- `server/`

  - `app/main.py` — inicialização FastAPI, CORS, routers, ciclo de vida, start do loop
  - `app/config.py` — settings (JWT, CORS, Redis URL)
  - `routes/health.py` — `GET /health`
  - `routes/auth.py` — `POST /auth/login` (dev: `demo@zerion.local` / `demo`) e `POST /auth/ticket` (gera ticket curto em Redis)
  - `auth/jwt.py` — criação e verificação de tokens JWT
  - `ws/endpoints.py` — `GET /ws` (subprotocols `zerion.v1` e `auth.<ticket>`), valida Origin, ping/pong, chat global com rate-limit, snapshots `state`
  - `game/loop.py` — loop autoritativo base (tick), estrutura para AoI/entidades
  - `game/aoi.py` — grade espacial simples (`GridAoI`) para área de interesse
  - `game/state.py` — montagem de snapshots mínimos
  - `services/redis.py` — gerenciador de Redis (singleton)
  - `requirements.txt` — libs Python (sem builds nativos no Windows; usa `u-msgpack-python`)
  - `Dockerfile` — imagem do backend

- `client/`

  - `src/app/layout.tsx` e `src/app/page.tsx` — App Router (Next 15)
  - `src/styles/globals.css` — Tailwind base
  - `tailwind.config.ts` + `postcss.config.js` — configuração (usa `@tailwindcss/postcss`)
  - `src/game/engine/PhaserGame.ts` — cena Phaser com overlay de chat e input buffer
  - `src/game/components/GameCanvas.tsx` — wrapper React do canvas
  - `src/game/net/protocol.ts` — tipagens mínimas do protocolo (client/server)
  - `src/game/net/socket.ts` — WS binário com `@msgpack/msgpack`, handshake por token
  - `src/game/events.ts` — event bus (chat, state, client chat/move)
  - `src/store/useGameStore.ts` — Zustand: login dev, conectar WS, ping, chat, move
  - `src/ui/Chat.tsx` — componente de chat (log + input)
  - `Dockerfile` — imagem do client
  - `package.json` — dependências (Next, React, Phaser, Zustand, @msgpack/msgpack, Tailwind)

- DevOps
  - `docker-compose.yml` — MySQL, Redis, Server, Client e Nginx
  - `ops/nginx.conf` — proxy (HTTP/WS) para client e server, repasse de Sec-WebSocket-Protocol e timeouts
  - `.env.example` — variáveis (JWT, MySQL, Redis)
  - `README.md` — instruções rápidas de execução
  - `.gitignore`

### Backend (FastAPI + WS)

- Auth/JWT (dev): `POST /auth/login` retorna um `access_token` válido para handshake via WS
- Health: `GET /health` → `{ status: "ok" }`
- WebSocket `/ws` (subprotocols `zerion.v1` e `auth.<ticket>`)
  - Cliente envia binário msgpack: `ping`, `chat`, `move`
  - Servidor responde:
    - `pong`: `{ t: "pong", ts }`
    - `event:msg`: `{ t: "event", type: "msg", payload: { channel, from, msg, ts } }`
    - `state`: `{ t: "state", seq, you: { x,y,hp,mp }, entities: [...] }` (mínimo, enviado ao `move`)
- Chat global
  - Com Redis: pub/sub (`chat:global`)
  - Sem Redis: fallback broadcast entre sockets ativos
- Serialização
  - Servidor: `u-msgpack-python` (puro Python, compatível Windows)
  - Cliente: `@msgpack/msgpack`
- Loop de jogo
  - `GameServer` com tick base (10 Hz) e placeholders para sistemas
  - `GridAoI` disponível para evolução de AoI/diffs de snapshot

### Frontend (Next 15 + TS + Tailwind + Phaser + Zustand)

- UI base com HUD simples: título, botões (Conectar/Ping/Desconectar), chat, canvas Phaser
- Conexão WS binária com handshake por ticket (obtido via `POST /auth/ticket`)
- Chat
  - Caixa de mensagens (React) e overlay no Phaser
  - Envio pelo input React e pelo canvas (buffer de texto + Enter)
- Movimento
  - Setas do teclado emitem `move` (placeholder) → servidor responde `state` → cena atualiza posição do jogador
- Tailwind (Next 15)
  - PostCSS via `@tailwindcss/postcss`

### Variáveis de ambiente

- Raiz (`.env` baseado em `.env.example`)
  - `JWT_SECRET`, `MYSQL_*`, `REDIS_URL`
- Client (`client/.env.local`)
  - `NEXT_PUBLIC_API_BASE=http://localhost:8000`
  - `NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws`

### Como rodar (sem Docker)

Backend:

```
cd server
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt
.venv/Scripts/python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Frontend:

```
cd client
npm install
npm run dev
```

URLs:

- App: http://localhost:3000
- API: http://localhost:8000/docs e http://localhost:8000/health

### Como rodar (Docker Compose)

Requer Docker instalado.

```
docker compose up --build
```

- Nginx: http://localhost:8080
- Client direto: http://localhost:3000
- Server direto: http://localhost:8000

### Protocolo WS — v0 (MVP)

- Handshake: subprotocols `["zerion.v1", "auth.<ticket>"]`
- Cliente → Servidor (msgpack):
  - `ping:{ t:"ping", ts? }`
  - `chat:{ t:"chat", channel:"global", msg }`
  - `move:{ t:"move", dx, dy, seq }` (placeholder)
- Servidor → Cliente (msgpack):
  - `pong:{ t:"pong", ts }`
  - `event:msg:{ t:"event", type:"msg", payload:{ channel, from, msg, ts } }`
  - `state:{ t:"state", seq, you:{x,y,hp,mp}, entities:[...] }`

### Próximos passos sugeridos

- Implementar diffs de snapshot por AoI (grid) e assinatura de células
- Persistência básica (pos/hp/mp/inventário) e spawn de NPC/monstros
- Movimentação autoritativa com colisão (Tiled map compartilhado)
- Predição/reconciliação no cliente (sequenciamento de inputs)
- UI: minimap, inventory, battle list, action bars
- Hardening de segurança (rate-limits, LoS, cooldowns) e observabilidade (métricas/logs)

### Notas

- Windows/Tooling: para evitar compilações nativas, o backend usa `u-msgpack-python`.
- Tailwind (Next 15): a configuração usa `@tailwindcss/postcss` em `postcss.config.js`.

### Critérios de aceitação (checagem rápida)

- POST `/auth/ticket` retorna 201 com `{ ticket, expires_at }` quando o Bearer é válido
- WS recusa conexão sem subprotocol válido, sem ticket ou Origin não permitido (fecha com 1008)
- Chat bloqueado acima de `RATE_CHAT_MAX` por usuário/min; cliente recebe `event:{ type:"warn", payload:{ code:"chat_rate_limited" } }`
- Login retorna 429 quando excede `RATE_LOGIN_MAX` por IP/min
- Cliente reconecta automaticamente após derrubar o server (backoff exponencial até 15s) e retoma `state/event` após reconectar
- Nginx repassa `Sec-WebSocket-Protocol` e mantém `proxy_read_timeout`/`proxy_send_timeout` (75s)

### Teste rápido ponta-a-ponta

1. Backend

```
cd server
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt
.venv/Scripts/python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

2. Frontend

```
cd client
npm install
npm run dev
```

3. Fluxo no app (http://localhost:3000):

- Clique "Conectar" (faz login dev, pega ticket e abre WS com subprotocols)
- Envie mensagens no chat; após ~20/min, ver `warn`
- Use setas para mandar `move` e ver o snapshot atualizar
- Reinicie o backend; confirme reconexão automática (após 1s, 2s, 4s...)
