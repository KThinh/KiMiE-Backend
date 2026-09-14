import sqlite3

from fastapi import APIRouter, Depends, HTTPException, status

from app.database import get_db
from app.deps import get_current_user, get_optional_user
from app.schemas import ReviewIn, ReviewListOut, ReviewOut

router = APIRouter(prefix="/api/products/{product_id}/reviews", tags=["reviews"])

REVIEW_SELECT = """
SELECT r.id, r.product_id, r.buyer_id, u.name AS buyer_name, r.rating, r.comment, r.created_at, r.updated_at
FROM reviews r JOIN users u ON u.id = r.buyer_id
"""


def _row_to_review(row: sqlite3.Row) -> ReviewOut:
    return ReviewOut(**dict(row))


def _get_product(db: sqlite3.Connection, product_id: int) -> sqlite3.Row:
    row = db.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy sản phẩm.")
    return row


@router.get("", response_model=ReviewListOut)
def list_reviews(
    product_id: int,
    user: sqlite3.Row | None = Depends(get_optional_user),
    db: sqlite3.Connection = Depends(get_db),
):
    product = _get_product(db, product_id)
    rows = db.execute(
        REVIEW_SELECT + " WHERE r.product_id = ? ORDER BY r.created_at DESC", (product_id,)
    ).fetchall()

    my_review = None
    if user is not None:
        mine = next((r for r in rows if r["buyer_id"] == user["id"]), None)
        if mine is not None:
            my_review = _row_to_review(mine)

    return ReviewListOut(
        average_rating=product["rating"],
        review_count=product["review_count"],
        items=[_row_to_review(r) for r in rows],
        my_review=my_review,
    )


@router.post("", response_model=ReviewOut, status_code=status.HTTP_201_CREATED)
def upsert_review(
    product_id: int,
    payload: ReviewIn,
    user: sqlite3.Row = Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db),
):
    product = _get_product(db, product_id)
    if product["seller_id"] == user["id"]:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Không thể tự đánh giá sản phẩm của chính mình.")

    db.execute(
        """INSERT INTO reviews (product_id, buyer_id, rating, comment)
           VALUES (?, ?, ?, ?)
           ON CONFLICT(product_id, buyer_id) DO UPDATE SET
               rating = excluded.rating,
               comment = excluded.comment,
               updated_at = CURRENT_TIMESTAMP""",
        (product_id, user["id"], payload.rating, payload.comment),
    )
    row = db.execute(
        REVIEW_SELECT + " WHERE r.product_id = ? AND r.buyer_id = ?", (product_id, user["id"])
    ).fetchone()
    return _row_to_review(row)


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_my_review(
    product_id: int,
    user: sqlite3.Row = Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db),
):
    _get_product(db, product_id)
    cur = db.execute("DELETE FROM reviews WHERE product_id = ? AND buyer_id = ?", (product_id, user["id"]))
    if cur.rowcount == 0:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Bạn chưa đánh giá sản phẩm này.")
