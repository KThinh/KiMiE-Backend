"""Hộ chiếu di sản — con dấu sưu tầm lưu theo từng tài khoản (trước đây nằm chung trong
localStorage của trình duyệt nên đổi tài khoản vẫn thấy dấu của người trước)."""

import psycopg
from fastapi import APIRouter, Depends, HTTPException, status

from app.database import get_db
from app.deps import get_current_user
from app.schemas import PassportOut, PassportStampIn

router = APIRouter(prefix="/api/passport", tags=["passport"])

# phải khớp danh sách STAMPS ở script.js của frontend
STAMP_IDS = {"bt", "vp", "pv", "expo", "relic", "read", "cart"}

CREATE_TABLE_SQL = """
    CREATE TABLE IF NOT EXISTS passport_stamps (
        user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        stamp_id   TEXT NOT NULL,
        earned_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (user_id, stamp_id)
    );
"""


def _load(db: psycopg.Connection, user_id: int) -> PassportOut:
    rows = db.execute(
        "SELECT stamp_id, earned_at FROM passport_stamps WHERE user_id = %s ORDER BY earned_at",
        (user_id,),
    ).fetchall()
    return PassportOut(stamps={r["stamp_id"]: r["earned_at"] for r in rows})


@router.get("", response_model=PassportOut)
def get_passport(user: dict = Depends(get_current_user), db: psycopg.Connection = Depends(get_db)):
    return _load(db, user["id"])


@router.post("/stamps", response_model=PassportOut)
def add_stamp(payload: PassportStampIn, user: dict = Depends(get_current_user), db: psycopg.Connection = Depends(get_db)):
    if payload.stamp_id not in STAMP_IDS:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Con dấu không hợp lệ.")
    db.execute(
        "INSERT INTO passport_stamps (user_id, stamp_id) VALUES (%s, %s) ON CONFLICT (user_id, stamp_id) DO NOTHING",
        (user["id"], payload.stamp_id),
    )
    return _load(db, user["id"])


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
def reset_passport(user: dict = Depends(get_current_user), db: psycopg.Connection = Depends(get_db)):
    db.execute("DELETE FROM passport_stamps WHERE user_id = %s", (user["id"],))
