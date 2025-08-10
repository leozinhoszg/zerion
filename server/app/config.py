import os
from pydantic import BaseModel


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
    database_url: str = os.getenv("DATABASE_URL", "mysql+asyncmy://root:root@mysql:3306/zerion_db")
    db_pool_size: int = int(os.getenv("DB_POOL_SIZE", "10"))
    db_max_overflow: int = int(os.getenv("DB_MAX_OVERFLOW", "10"))
    db_pool_timeout: int = int(os.getenv("DB_POOL_TIMEOUT", "30"))
    db_pool_recycle: int = int(os.getenv("DB_POOL_RECYCLE", "1800"))
    dev_login_fallback: bool = os.getenv("DEV_LOGIN_FALLBACK", "false").lower() == "true"


def get_settings() -> Settings:
    return Settings()



