"""Kết nối PostgreSQL dùng chung cho các router. Dùng psycopg (v3) thuần (không ORM)
để khớp 1-1 với create_db.py/database-schema.md — mọi logic (kể cả trigger tự cập
nhật tồn kho/đã bán) đều đã nằm sẵn trong database, không cần định nghĩa lại.

row_factory=dict_row để mỗi dòng trả về là 1 dict thường (row["ten_cot"], dict(row)...)
— giữ đúng cách truy cập mà serializers.py/các router đã dùng từ hồi còn sqlite3.Row."""

from contextlib import contextmanager

import psycopg
from psycopg.rows import dict_row

from app.config import DATABASE_URL


def _connect() -> psycopg.Connection:
    if not DATABASE_URL:
        raise RuntimeError(
            "Chưa đặt KV_DATABASE_URL — xem .env.example để biết cách lấy chuỗi kết nối "
            "PostgreSQL từ Render rồi đặt vào file .env."
        )
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)


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
