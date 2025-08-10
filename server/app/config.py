import os
from pydantic import BaseModel, Field

# URL padrão do banco (usada quando nenhuma variável de ambiente é fornecida)
DEFAULT_DATABASE_URL = "mysql+asyncmy://root:root@mysql:3306/zerion_db"


class Settings(BaseModel):
    environment: str = os.getenv("ENV", "development")
    jwt_secret: str = os.getenv("JWT_SECRET", "dev-secret-change-me")
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    redis_url: str = os.getenv("REDIS_URL", "redis://redis:6379/0")
    cors_origins: list[str] = [
        os.getenv("CORS_ORIGIN", "http://localhost:3000"),
        "http://localhost:8080",
    ]
    allowed_ws_origins: list[str] = [
        os.getenv("ALLOWED_WS_ORIGINS", "http://localhost:3000").split(",")[0],
        "http://localhost:8080",
    ]
    ticket_ttl_seconds: int = int(os.getenv("TICKET_TTL_SECONDS", "60"))
    rate_login_max: int = int(os.getenv("RATE_LOGIN_MAX", "10"))
    rate_chat_max: int = int(os.getenv("RATE_CHAT_MAX", "20"))
    database_url: str = Field(default_factory=lambda: os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL))
    db_pool_size: int = int(os.getenv("DB_POOL_SIZE", "10"))
    db_max_overflow: int = int(os.getenv("DB_MAX_OVERFLOW", "10"))
    db_pool_timeout: int = int(os.getenv("DB_POOL_TIMEOUT", "30"))
    db_pool_recycle: int = int(os.getenv("DB_POOL_RECYCLE", "1800"))
    dev_login_fallback: bool = os.getenv("DEV_LOGIN_FALLBACK", "false").lower() == "true"


def _apply_driver_fallback() -> None:
    """
    Fallback: em Windows, se a URL usa asyncmy e o driver não estiver disponível,
    trocamos para o driver assíncrono "aiomysql" para manter compatibilidade com create_async_engine.
    Também cobre o caso onde a variável de ambiente não está definida (usa DEFAULT_DATABASE_URL).
    """
    try:
        import asyncmy  # type: ignore  # noqa: F401
        return
    except Exception:
        pass

    if os.name == "nt":
        url = os.getenv("DATABASE_URL") or DEFAULT_DATABASE_URL
        if url.startswith("mysql+asyncmy://"):
            os.environ["DATABASE_URL"] = url.replace("mysql+asyncmy://", "mysql+aiomysql://", 1)


_apply_driver_fallback()


def get_settings() -> Settings:
    return Settings()



