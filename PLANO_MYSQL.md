## Plano de Integração do MySQL no Zerion

### Objetivo e escopo

- **Objetivo**: ativar persistência real no backend com MySQL, mantendo Redis para tickets, rate-limit e chat (pub/sub).
- **Escopo do MVP**: contas de usuário e personagem (registro, login real, criação de personagem, posição/atributos persistidos e restabelecidos ao reconectar).

### Topologia e credenciais (dev)

- **Banco**: MySQL 8.x, schema `zerion_db`.
- **Credenciais locais (fornecidas)**:
  - user: `root`
  - password: `Jae66yrr@` (observação: `@` deve ser URL-encodado: `%40`)
  - host: `127.0.0.1`
  - porta: `3306`
- **DATABASE_URL (local)**: `mysql+asyncmy://root:Jae66yrr%40@127.0.0.1:3306/zerion_db`
- **Compose (dev com Docker)**: service name `mysql` como host; credenciais padrão do compose ou variáveis via `.env`.
- **Charset/Collation**: `utf8mb4` e `utf8mb4_0900_ai_ci` (ou `utf8mb4_unicode_ci`).

## Dependências (backend/server)

- `SQLAlchemy>=2.0`
- `asyncmy>=0.2`
- `alembic>=1.13`
- `passlib[bcrypt]`

Após editar `server/requirements.txt`, rebuild do container do `server` quando usar Docker.

### Configuração de ambiente

- Adicionar em `server/app/config.py`:
  - `database_url: str = os.getenv("DATABASE_URL", "mysql+asyncmy://root:root@mysql:3306/zerion_db")`
  - (Opcional) `db_pool_size`, `db_max_overflow`, `db_pool_timeout`.
- Atualizar `.env.example` (raiz):

```
DATABASE_URL=mysql+asyncmy://root:root@mysql:3306/zerion_db
# Exemplo local (senha com @ precisa de %40):
# DATABASE_URL=mysql+asyncmy://root:Jae66yrr%40@127.0.0.1:3306/zerion_db
```

## Serviço de DB (engine e sessão)

- Criar `server/services/db.py` com:
  - `create_async_engine(settings.database_url, pool_pre_ping=True, pool_size=10, max_overflow=10)`
  - `async_sessionmaker(expire_on_commit=False)`
  - Dependency FastAPI `get_db()` para injetar sessões por request/task.
- No `lifespan` do app, opcionalmente testar conexão (SELECT 1) e fechar engine no shutdown.

Exemplo (esqueleto):

```python
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from contextlib import asynccontextmanager
from app.config import get_settings

settings = get_settings()
engine = create_async_engine(settings.database_url, pool_pre_ping=True)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

@asynccontextmanager
async def get_db():
    session: AsyncSession = AsyncSessionLocal()
    try:
        yield session
    finally:
        await session.close()
```

## Modelagem (MVP)

### Tabelas

- `users`

  - `id` (PK, BIGINT AUTO_INCREMENT)
  - `email` (VARCHAR(255), UNIQUE, INDEX)
  - `password_hash` (VARCHAR(255))
  - `created_at` (TIMESTAMP, default CURRENT_TIMESTAMP)
  - `flags_json` (JSON, opcional)

- `characters`
  - `id` (PK, BIGINT AUTO_INCREMENT)
  - `user_id` (FK -> users.id, INDEX)
  - `name` (VARCHAR(32))
  - `class` (VARCHAR(32))
  - `level` (INT, default 1)
  - `xp` (BIGINT, default 0)
  - `map` (VARCHAR(64))
  - `x` (INT, default 0)
  - `y` (INT, default 0)
  - `hp` (INT, default 100)
  - `mp` (INT, default 50)
  - `attrs_json` (JSON)
  - `last_login_at` (TIMESTAMP NULL)
  - `updated_at` (TIMESTAMP, default CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP)

Chaves/índices: UNIQUE `(user_id, name)` se quisermos restringir nomes por usuário; FKs com ON DELETE RESTRICT (ou CASCADE, conforme política).

## Migrações (Alembic)

### Inicialização

```
cd server
alembic init alembic
```

- Configurar `alembic.ini` para usar `DATABASE_URL` via env ou `sqlalchemy.url`.
- No `alembic/env.py`, apontar para o `metadata` dos models (SQLAlchemy) para autogenerate.

### Criar migração inicial

```
alembic revision -m "init" --autogenerate
alembic upgrade head
```

### Execução em Docker

- Opção A: executar `alembic upgrade head` manualmente dentro do container do `server`.
- Opção B: criar um serviço `migrate` no `docker-compose` que roda a migração e sai antes do `server` subir.
- Opção C: adicionar um entrypoint no `server` que roda a migração em dev antes do `uvicorn` (simples para desenvolvimento).

## Repositórios e Schemas

- Diretório `server/services/repositories/`:
  - `user_repository.py`: `create_user`, `get_user_by_email`, `verify_credentials`.
  - `character_repository.py`: `get_default_character_for_user`, `create_default_character`, `update_position`.
- Diretório `server/app/schemas/` (Pydantic): DTOs para requests/responses (`UserCreate`, `LoginRequest/Response`, `CharacterDTO`).

## Integração nas rotas e WS

### Auth (`server/routes/auth.py`)

- Adicionar `POST /auth/register` para criar usuário (hash com `passlib[bcrypt]`).
- Alterar `POST /auth/login` para autenticar via DB (remover login dev; manter feature-flag temporária, ex.: `DEV_LOGIN_FALLBACK=true`).
- `POST /auth/ticket` deve usar o `user_id` real do DB para emitir ticket (Redis permanece).

### WebSocket (`server/ws/endpoints.py`)

- No handshake aceito, carregar personagem do usuário:
  - Se existir, usar posição/atributos persistidos.
  - Se não existir, criar personagem padrão (spawn inicial).
- No `move`, atualizar `you` em memória e persistir no DB:
  - MVP: persistir a cada `move` (simplicidade).
  - Evolução: flush periódico (ex.: a cada 5s) ou on-disconnect.

## Seeds (ambiente de dev)

- Script `server/scripts/seed_dev.py` que cria:
  - Usuário demo: `demo@zerion.local` / senha `demo`.
  - Personagem inicial vinculado ao usuário.
- Execução manual ou automática em dev.

## Operação e observabilidade

- Pool de conexão: `pool_size=10`, `max_overflow=10`, `pool_pre_ping=True`.
- Tratamento de erros: capturar `DBAPIError`/`IntegrityError` e retornar 400/409 adequados.
- Métricas (futuro): contadores de queries, histogramas de latência.

## Segurança

- Não usar `root` em produção. Criar usuário dedicado `zerion_app` com privilégios limitados ao schema `zerion_db`.
- Guardar segredos (senha DB, `JWT_SECRET`) somente em variáveis de ambiente.
- Sanitização e rate-limit já presentes; auditar mensagens e payloads.

## Documentação e DX

- Atualizar `README.md` e `.env.example` com `DATABASE_URL` e comandos Alembic.
- Notas para Windows: lembrar de URL-encoding em senhas (ex.: `@` → `%40`).

## Critérios de aceitação

- `alembic upgrade head` cria `users` e `characters` com índices e FKs.
- `POST /auth/register` retorna 201 e persiste usuário.
- `POST /auth/login` autentica via DB e retorna JWT válido.
- `POST /auth/ticket` emite ticket com `user_id` real.
- WS: ao conectar, carrega personagem e envia `state` com posição persistida; após `move`, posição persiste e é restaurada ao reconectar.
- Health estendido pode checar DB (opcional): retorna `db: ok` quando ping responde.

## Plano de execução (ordem sugerida)

1. Adicionar dependências e `DATABASE_URL` em `config`.
2. Implementar `services/db.py` (engine/sessão) + health check simples.
3. Criar models (`users`, `characters`) e inicializar Alembic; gerar migração inicial e aplicar.
4. Implementar repositories + schemas Pydantic.
5. Atualizar rotas: `register` e `login` via DB.
6. Ajustar WS: carregar/persistir personagem.
7. Criar seeds de dev e atualizar README/.env.example.
8. Testes manuais ponta-a-ponta (HTTP + WS) e validação de critérios de aceitação.

## Exemplos de `DATABASE_URL`

- Local (credenciais fornecidas):

```
mysql+asyncmy://root:Jae66yrr%40@127.0.0.1:3306/zerion_db
```

- Docker (compose atual — `root:root`, host `mysql`):

```
mysql+asyncmy://root:root@mysql:3306/zerion_db
```

## Comandos úteis

### Sem Docker

```
cd server
python -m venv .venv
.venv/Scripts/activate  # Windows
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Com Docker Compose

```
docker compose up --build
# (Opcional) executar migrações dentro do container do server
docker compose exec server alembic upgrade head
```

