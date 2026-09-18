import psycopg

from fastapi import APIRouter, Depends, HTTPException, status

from app.database import get_db
from app.deps import get_current_user
from app.schemas import AddressIn, AddressOut

router = APIRouter(prefix="/api/addresses", tags=["addresses"])


def _row_to_address(row: dict) -> AddressOut:
    return AddressOut(**dict(row))


def _owned_address(db: psycopg.Connection, address_id: int, user_id: int) -> dict:
    row = db.execute("SELECT * FROM addresses WHERE id = %s", (address_id,)).fetchone()
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy địa chỉ này.")
    if row["user_id"] != user_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Đây không phải địa chỉ của bạn.")
    return row


@router.get("", response_model=list[AddressOut])
def list_addresses(user: dict = Depends(get_current_user), db: psycopg.Connection = Depends(get_db)):
    rows = db.execute(
        "SELECT * FROM addresses WHERE user_id = %s ORDER BY is_default DESC, created_at DESC", (user["id"],)
    ).fetchall()
    return [_row_to_address(r) for r in rows]


def _clear_default(db: psycopg.Connection, user_id: int) -> None:
    db.execute("UPDATE addresses SET is_default = false WHERE user_id = %s", (user_id,))


@router.post("", response_model=AddressOut, status_code=status.HTTP_201_CREATED)
def create_address(payload: AddressIn, user: dict = Depends(get_current_user), db: psycopg.Connection = Depends(get_db)):
    if payload.is_default:
        _clear_default(db, user["id"])
    cur = db.execute(
        """INSERT INTO addresses (user_id, label, recipient_name, phone, address_line, is_default)
           VALUES (%s, %s, %s, %s, %s, %s) RETURNING id""",
        (user["id"], payload.label, payload.recipient_name, payload.phone, payload.address_line, payload.is_default),
    )
    new_id = cur.fetchone()["id"]
    row = db.execute("SELECT * FROM addresses WHERE id = %s", (new_id,)).fetchone()
    return _row_to_address(row)


@router.put("/{address_id}", response_model=AddressOut)
def update_address(address_id: int, payload: AddressIn, user: dict = Depends(get_current_user), db: psycopg.Connection = Depends(get_db)):
    _owned_address(db, address_id, user["id"])
    if payload.is_default:
        _clear_default(db, user["id"])
    db.execute(
        """UPDATE addresses SET label = %s, recipient_name = %s, phone = %s, address_line = %s, is_default = %s
           WHERE id = %s""",
        (payload.label, payload.recipient_name, payload.phone, payload.address_line, payload.is_default, address_id),
    )
    row = db.execute("SELECT * FROM addresses WHERE id = %s", (address_id,)).fetchone()
    return _row_to_address(row)


@router.patch("/{address_id}/default", response_model=AddressOut)
def set_default_address(address_id: int, user: dict = Depends(get_current_user), db: psycopg.Connection = Depends(get_db)):
    _owned_address(db, address_id, user["id"])
    _clear_default(db, user["id"])
    db.execute("UPDATE addresses SET is_default = true WHERE id = %s", (address_id,))
    row = db.execute("SELECT * FROM addresses WHERE id = %s", (address_id,)).fetchone()
    return _row_to_address(row)


@router.delete("/{address_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_address(address_id: int, user: dict = Depends(get_current_user), db: psycopg.Connection = Depends(get_db)):
    _owned_address(db, address_id, user["id"])
    db.execute("DELETE FROM addresses WHERE id = %s", (address_id,))
