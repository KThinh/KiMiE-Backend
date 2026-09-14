"""Kết nối SQLite dùng chung cho các router. Dùng sqlite3 thuần (không ORM) để
khớp 1-1 với create_db.py/database-schema.md — mọi logic (kể cả trigger tự cập
nhật tồn kho/đã bán) đều đã nằm sẵn trong file .db, không cần định nghĩa lại."""

import sqlite3
from contextlib import contextmanager

from app.config import DB_PATH


def _connect() -> sqlite3.Connection:
    # check_same_thread=False: FastAPI chạy các dependency đồng bộ (get_db, get_current_user, ...)
    # trong threadpool — cùng 1 request có thể "ghé" nhiều thread worker khác nhau khi resolve
    # dependency, dù chỉ 1 thread đụng vào connection tại 1 thời điểm (không có race thật sự).
    # Mặc định check_same_thread=True của sqlite3 chặn cả trường hợp an toàn này.
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def get_db():
    """FastAPI dependency: yield 1 connection/request, commit nếu không lỗi,
    rollback nếu có exception, luôn đóng lại sau khi request xong."""
    conn = _connect()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


@contextmanager
def db_session():
    """Dùng ngoài request FastAPI (vd. script seed/migrate) — cùng hành vi commit/rollback."""
    conn = _connect()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
