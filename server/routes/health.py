from fastapi import APIRouter
from services.db import test_db

router = APIRouter()


@router.get("/health")
async def health():
    db_ok = await test_db()
    return {"status": "ok", "db": "ok" if db_ok else "down"}




