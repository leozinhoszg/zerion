from __future__ import annotations

import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from sqlalchemy import create_engine
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from alembic import context

# Interpret the config file for Python logging.
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Importar metadata dos models
from models.base import Base  # noqa: E402
from models.user import User  # noqa: F401,E402
from models.character import Character  # noqa: F401,E402

target_metadata = Base.metadata


def get_url() -> str:
    url = os.getenv("DATABASE_URL")
    if not url:
        # fallback ao alembic.ini se necessário
        url = config.get_main_option("sqlalchemy.url")
    if not url:
        raise RuntimeError("DATABASE_URL não definido e sqlalchemy.url vazio no alembic.ini")
    return url


def run_migrations_offline() -> None:
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    url = get_url()

    connectable = create_engine(url) if not url.startswith("mysql+asyncmy") else create_async_engine(url)

    if isinstance(connectable, AsyncEngine):
        async def do_run_migrations() -> None:
            async with connectable.connect() as connection:
                await connection.run_sync(_run_sync)
        import asyncio
        asyncio.run(do_run_migrations())
    else:
        with connectable.connect() as connection:
            _run_sync(connection)


def _run_sync(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()



