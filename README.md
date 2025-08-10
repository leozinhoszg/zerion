## Zerion Monorepo (MVP)

Projeto inicial baseado no documento `projeto zerion.md`.

### Estrutura

- `server/` — FastAPI (HTTP/WS) + esqueleto do loop de jogo autoritativo
- `client/` — Next.js (TypeScript + App Router + Tailwind)
- `ops/nginx.conf` — Proxy para `client` e `server` (inclui WS)
- `docker-compose.yml` — MySQL, Redis, Server, Client e Nginx

### Requisitos

- Docker e Docker Compose
- Alternativa sem Docker: Node 18+ e Python 3.11+

### Variáveis de ambiente

Copie `.env.example` para `.env` na raiz e ajuste conforme necessário:

```
cp .env.example .env
```

Principais chaves:

- `JWT_SECRET`
- `MYSQL_*`
- `REDIS_URL`
- `DATABASE_URL` (ex.: `mysql+asyncmy://root:root@mysql:3306/zerion_db`)


### Rodando com Docker Compose

```
docker compose up --build
```

Serviços:

- Nginx: http://localhost:8080 (proxy para client e server)
- Client direto: http://localhost:3000
- Server direto: http://localhost:8000/docs

### Backend (server) — dev sem Docker

```
cd server
python -m venv .venv
source .venv/bin/activate  # Windows (PowerShell): .venv\\Scripts\\Activate.ps1
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend (client) — dev sem Docker

```
cd client
npm install
npm run dev
```

### Endpoints úteis

- Healthcheck: `GET /health` → `{ "status": "ok" }`
- Login: `POST /auth/login` → `{ access_token, token_type }` (dev: aceita email/senha demo)
- Ticket WS: `POST /auth/ticket` (Bearer) → `{ ticket, expires_at }`
- WebSocket: abrir com subprotocols `["zerion.v1", "auth.<ticket>"]`

### Próximos passos

- Integrar DB/Redis reais nas rotas (SQLAlchemy Async e Redis asyncio)
- Implementar diffs/AoI no WS, rate-limits e CSRF nas rotas HTTP
- Cliente: adicionar Phaser, Zustand, Query e HUD inicial
