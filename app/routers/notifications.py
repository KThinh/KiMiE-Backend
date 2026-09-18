import psycopg

from fastapi import APIRouter, Depends

from app.database import get_db
from app.deps import get_current_user
from app.schemas import NotificationOut

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


@router.get("", response_model=list[NotificationOut])
def list_notifications(user: dict = Depends(get_current_user), db: psycopg.Connection = Depends(get_db)):
    rows = db.execute(
        "SELECT * FROM notifications WHERE user_id = %s ORDER BY created_at DESC LIMIT 100", (user["id"],)
    ).fetchall()
    return [NotificationOut(**dict(r)) for r in rows]


@router.patch("/{notification_id}/read", response_model=NotificationOut)
def mark_read(notification_id: int, user: dict = Depends(get_current_user), db: psycopg.Connection = Depends(get_db)):
    db.execute(
        "UPDATE notifications SET is_read = true WHERE id = %s AND user_id = %s", (notification_id, user["id"])
    )
    row = db.execute("SELECT * FROM notifications WHERE id = %s", (notification_id,)).fetchone()
    return NotificationOut(**dict(row))


@router.patch("/read-all", status_code=204)
def mark_all_read(user: dict = Depends(get_current_user), db: psycopg.Connection = Depends(get_db)):
    db.execute("UPDATE notifications SET is_read = true WHERE user_id = %s AND is_read = false", (user["id"],))
