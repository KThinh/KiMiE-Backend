import psycopg

from fastapi import APIRouter, Depends, HTTPException, status

from app.database import get_db
from app.deps import get_current_user
from app.schemas import (
    ChangePasswordIn,
    ResetPasswordIn,
    TokenOut,
    UserLoginIn,
    UserOut,
    UserRegisterIn,
    UserUpdateIn,
)
from app.security import create_access_token, hash_password, verify_password
from app.serializers import row_to_user

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=TokenOut, status_code=status.HTTP_201_CREATED)
def register(payload: UserRegisterIn, db: psycopg.Connection = Depends(get_db)):
    if db.execute("SELECT id FROM users WHERE username = %s", (payload.username,)).fetchone() is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Tên đăng nhập này đã được sử dụng.")
    if db.execute("SELECT id FROM users WHERE email = %s", (payload.email,)).fetchone() is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Email này đã được đăng ký.")
    cur = db.execute(
        """INSERT INTO users (name, username, email, phone, password_hash, is_seller)
           VALUES (%s, %s, %s, %s, %s, 0) RETURNING id""",
        (payload.name, payload.username, payload.email, payload.phone, hash_password(payload.password)),
    )
    new_id = cur.fetchone()["id"]
    user = db.execute("SELECT * FROM users WHERE id = %s", (new_id,)).fetchone()
    return TokenOut(access_token=create_access_token(user["id"]), user=row_to_user(db, user))


@router.post("/login", response_model=TokenOut)
def login(payload: UserLoginIn, db: psycopg.Connection = Depends(get_db)):
    user = db.execute("SELECT * FROM users WHERE username = %s", (payload.username,)).fetchone()
    if user is None or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Tên đăng nhập hoặc mật khẩu không đúng.")
    return TokenOut(access_token=create_access_token(user["id"]), user=row_to_user(db, user))


@router.get("/me", response_model=UserOut)
def me(user: dict = Depends(get_current_user), db: psycopg.Connection = Depends(get_db)):
    return row_to_user(db, user)


@router.patch("/me", response_model=UserOut)
def update_me(
    payload: UserUpdateIn,
    user: dict = Depends(get_current_user),
    db: psycopg.Connection = Depends(get_db),
):
    if payload.email is not None and payload.email != user["email"]:
        clash = db.execute("SELECT id FROM users WHERE email = %s AND id != %s", (payload.email, user["id"])).fetchone()
        if clash is not None:
            raise HTTPException(status.HTTP_409_CONFLICT, "Email này đã được dùng bởi tài khoản khác.")

    db.execute(
        """UPDATE users SET
               name = %s, email = %s, phone = %s, avatar_url = %s
           WHERE id = %s""",
        (
            payload.name if payload.name is not None else user["name"],
            payload.email if payload.email is not None else user["email"],
            payload.phone if payload.phone is not None else user["phone"],
            payload.avatar_url if payload.avatar_url is not None else user["avatar_url"],
            user["id"],
        ),
    )
    fresh = db.execute("SELECT * FROM users WHERE id = %s", (user["id"],)).fetchone()
    return row_to_user(db, fresh)


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(
    payload: ChangePasswordIn,
    user: dict = Depends(get_current_user),
    db: psycopg.Connection = Depends(get_db),
):
    if not verify_password(payload.current_password, user["password_hash"]):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Mật khẩu hiện tại không đúng.")
    db.execute("UPDATE users SET password_hash = %s WHERE id = %s", (hash_password(payload.new_password), user["id"]))


@router.post("/reset-password", status_code=status.HTTP_204_NO_CONTENT)
def reset_password(payload: ResetPasswordIn, db: psycopg.Connection = Depends(get_db)):
    """Quên mật khẩu — không yêu cầu đăng nhập. Chỉ xác định tài khoản qua username
    (đã UNIQUE trong bảng users), không có bước xác thực email/OTP nào khác."""
    if payload.new_password != payload.confirm_password:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Mật khẩu nhập lại không khớp.")
    user = db.execute("SELECT id FROM users WHERE username = %s", (payload.username,)).fetchone()
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy tài khoản với tên đăng nhập này.")
    db.execute("UPDATE users SET password_hash = %s WHERE id = %s", (hash_password(payload.new_password), user["id"]))
