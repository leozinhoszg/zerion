from __future__ import annotations

from sqlalchemy import BigInteger, String, TIMESTAMP, JSON, func
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[object] = mapped_column(TIMESTAMP, server_default=func.current_timestamp())
    flags_json: Mapped[object | None] = mapped_column(JSON, nullable=True)



