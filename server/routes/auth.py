from typing import Annotated

from fastapi import APIRouter, HTTPException, status, Depends, Header, Request
from pydantic import BaseModel, EmailStr

from auth.jwt import create_access_token, verify_access_token
from services.redis import issue_ws_ticket
from app.config import get_settings
from utils.ratelimit import allow
from services.db import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from services.repositories.user_repository import create_user, get_user_by_email, verify_credentials
from schemas.auth import RegisterRequest, LoginRequest as RealLoginRequest, TokenResponse


router = APIRouter()


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, request: Request):
    async with get_db() as session:
        existing = await get_user_by_email(session, body.email)
        if existing:
            raise HTTPException(status_code=409, detail="Email já registrado")
        await create_user(session, body.email, body.password)
        await session.commit()
    return {"status": "created"}


@router.post("/login", response_model=TokenResponse)
async def login(body: RealLoginRequest, request: Request):
    settings = get_settings()
    ip = request.client.host if request.client else "unknown"
    if not await allow(f"rl:login:{ip}", settings.rate_login_max):
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Muitas tentativas")
    # Auth via DB (com fallback opcional em dev se desejado futuramente)
    async with get_db() as session:
        user = await verify_credentials(session, body.email, body.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciais inválidas")
    token = create_access_token(subject=str(user.id))
    return TokenResponse(access_token=token)  # type: ignore[call-arg]


class TicketResponse(BaseModel):
    ticket: str
    expires_at: int


@router.post("/ticket", response_model=TicketResponse, status_code=status.HTTP_201_CREATED)
async def ticket(request: Request, authorization: str | None = Header(default=None)):
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Bearer token ausente")
    token = authorization.split(" ", 1)[1]
    payload = verify_access_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")
    user = payload.get("sub")
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")
    settings = get_settings()
    t = await issue_ws_ticket(user_id=int(user), ttl=settings.ticket_ttl_seconds)
    return TicketResponse(ticket=t, expires_at=int((settings.ticket_ttl_seconds) * 1000))



