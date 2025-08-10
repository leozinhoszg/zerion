from __future__ import annotations

from sqlalchemy import BigInteger, String, Integer, JSON, ForeignKey, TIMESTAMP, func
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class Character(Base):
    __tablename__ = "characters"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(32))
    class_name: Mapped[str] = mapped_column("class", String(32))
    level: Mapped[int] = mapped_column(Integer, default=1)
    xp: Mapped[int] = mapped_column(BigInteger, default=0)
    map: Mapped[str] = mapped_column(String(64), default="start")
    x: Mapped[int] = mapped_column(Integer, default=0)
    y: Mapped[int] = mapped_column(Integer, default=0)
    hp: Mapped[int] = mapped_column(Integer, default=100)
    mp: Mapped[int] = mapped_column(Integer, default=50)
    attrs_json: Mapped[object | None] = mapped_column(JSON, nullable=True)
    last_login_at: Mapped[object | None] = mapped_column(TIMESTAMP, nullable=True)
    updated_at: Mapped[object] = mapped_column(TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp())



