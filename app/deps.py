"""FastAPI dependencies dùng chung: lấy user hiện tại từ JWT, bắt buộc phải là seller."""

import sqlite3

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.database import get_db
from app.security import decode_access_token

# auto_error=False để tự trả lỗi 401 rõ ràng bằng tiếng Việt thay vì lỗi mặc định
_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: sqlite3.Connection = Depends(get_db),
) -> sqlite3.Row:
    if creds is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Vui lòng đăng nhập.")
    try:
        user_id = decode_access_token(creds.credentials)
    except jwt.PyJWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Phiên đăng nhập không hợp lệ hoặc đã hết hạn.")
    user = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Tài khoản không tồn tại.")
    return user


def get_optional_user(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: sqlite3.Connection = Depends(get_db),
) -> sqlite3.Row | None:
    if creds is None:
        return None
    try:
        user_id = decode_access_token(creds.credentials)
    except jwt.PyJWTError:
        return None
    return db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()


def require_seller(user: sqlite3.Row = Depends(get_current_user)) -> sqlite3.Row:
    if not user["is_seller"]:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Chỉ người bán mới thực hiện được thao tác này.")
    return user
