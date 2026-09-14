import sqlite3

from fastapi import APIRouter, Depends

from app.database import get_db
from app.schemas import VillageOut

router = APIRouter(prefix="/api/villages", tags=["villages"])


@router.get("", response_model=list[VillageOut])
def list_villages(db: sqlite3.Connection = Depends(get_db)):
    rows = db.execute("SELECT * FROM villages ORDER BY id").fetchall()
    return [VillageOut(**dict(r)) for r in rows]
