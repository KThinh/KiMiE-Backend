import sqlite3

from fastapi import APIRouter, Depends, HTTPException, status

from app.database import get_db
from app.deps import get_current_user
from app.schemas import TokenOut, UserLoginIn, UserOut, UserRegisterIn
from app.security import create_access_token, hash_password, verify_password
from app.serializers import row_to_user

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=TokenOut, status_code=status.HTTP_201_CREATED)
def register(payload: UserRegisterIn, db: sqlite3.Connection = Depends(get_db)):
    existing = db.execute("SELECT id FROM users WHERE email = ?", (payload.email,)).fetchone()
    if existing is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Email này đã được đăng ký.")
    cur = db.execute(
        "INSERT INTO users (name, email, phone, password_hash, is_seller) VALUES (?, ?, ?, ?, 0)",
        (payload.name, payload.email, payload.phone, hash_password(payload.password)),
    )
    user = db.execute("SELECT * FROM users WHERE id = ?", (cur.lastrowid,)).fetchone()
    return TokenOut(access_token=create_access_token(user["id"]), user=row_to_user(db, user))


@router.post("/login", response_model=TokenOut)
def login(payload: UserLoginIn, db: sqlite3.Connection = Depends(get_db)):
    user = db.execute("SELECT * FROM users WHERE email = ?", (payload.email,)).fetchone()
    if user is None or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Email hoặc mật khẩu không đúng.")
    return TokenOut(access_token=create_access_token(user["id"]), user=row_to_user(db, user))


@router.get("/me", response_model=UserOut)
def me(user: sqlite3.Row = Depends(get_current_user), db: sqlite3.Connection = Depends(get_db)):
    return row_to_user(db, user)
