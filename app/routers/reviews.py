import psycopg

from fastapi import APIRouter, Depends, HTTPException, status

from app.database import get_db
from app.deps import get_current_user, get_optional_user
from app.schemas import MyReviewOut, ReviewIn, ReviewListOut, ReviewOut

router = APIRouter(prefix="/api/products/{product_id}/reviews", tags=["reviews"])
me_router = APIRouter(prefix="/api/reviews", tags=["reviews"])


@me_router.get("/me", response_model=list[MyReviewOut])
def my_reviews(user: dict = Depends(get_current_user), db: psycopg.Connection = Depends(get_db)):
    rows = db.execute(
        """SELECT r.id, r.product_id, p.name AS product_name, p.image_url AS product_image,
                  r.rating, r.comment, r.created_at, r.updated_at,
                  COALESCE(
                      (SELECT array_agg(ri.image_url ORDER BY ri.id) FROM review_images ri WHERE ri.review_id = r.id),
                      ARRAY[]::text[]
                  ) AS images
           FROM reviews r JOIN products p ON p.id = r.product_id
           WHERE r.buyer_id = %s ORDER BY r.created_at DESC""",
        (user["id"],),
    ).fetchall()
    out = []
    for r in rows:
        d = dict(r); d["images"] = list(d["images"] or [])
        out.append(MyReviewOut(**d))
    return out

REVIEW_SELECT = """
SELECT r.id, r.product_id, r.buyer_id, u.name AS buyer_name, r.rating, r.comment, r.created_at, r.updated_at,
       COALESCE(
           (SELECT array_agg(ri.image_url ORDER BY ri.id) FROM review_images ri WHERE ri.review_id = r.id),
           ARRAY[]::text[]
       ) AS images
FROM reviews r JOIN users u ON u.id = r.buyer_id
"""


def _row_to_review(row: dict) -> ReviewOut:
    d = dict(row)
    d["images"] = list(d["images"] or [])
    return ReviewOut(**d)


def _get_product(db: psycopg.Connection, product_id: int) -> dict:
    row = db.execute("SELECT * FROM products WHERE id = %s", (product_id,)).fetchone()
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy sản phẩm.")
    return row


@router.get("", response_model=ReviewListOut)
def list_reviews(
    product_id: int,
    user: dict | None = Depends(get_optional_user),
    db: psycopg.Connection = Depends(get_db),
):
    product = _get_product(db, product_id)
    rows = db.execute(
        REVIEW_SELECT + " WHERE r.product_id = %s ORDER BY r.created_at DESC", (product_id,)
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
    user: dict = Depends(get_current_user),
    db: psycopg.Connection = Depends(get_db),
):
    product = _get_product(db, product_id)
    if product["seller_id"] == user["id"]:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Không thể tự đánh giá sản phẩm của chính mình.")

    purchased = db.execute(
        """SELECT 1 FROM order_items oi JOIN orders o ON o.id = oi.order_id
           WHERE o.buyer_id = %s AND oi.product_id = %s AND oi.item_status = 'delivered'
           LIMIT 1""",
        (user["id"], product_id),
    ).fetchone()
    if purchased is None:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "Bạn chỉ có thể đánh giá sản phẩm đã mua và nhận hàng thành công.",
        )

    cur = db.execute(
        """INSERT INTO reviews (product_id, buyer_id, rating, comment)
           VALUES (%s, %s, %s, %s)
           ON CONFLICT(product_id, buyer_id) DO UPDATE SET
               rating = excluded.rating,
               comment = excluded.comment,
               updated_at = CURRENT_TIMESTAMP
           RETURNING id""",
        (product_id, user["id"], payload.rating, payload.comment),
    )
    review_id = cur.fetchone()["id"]
    db.execute("DELETE FROM review_images WHERE review_id = %s", (review_id,))
    for url in payload.images:
        db.execute("INSERT INTO review_images (review_id, image_url) VALUES (%s, %s)", (review_id, url))

    row = db.execute(REVIEW_SELECT + " WHERE r.id = %s", (review_id,)).fetchone()
    return _row_to_review(row)


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_my_review(
    product_id: int,
    user: dict = Depends(get_current_user),
    db: psycopg.Connection = Depends(get_db),
):
    _get_product(db, product_id)
    cur = db.execute("DELETE FROM reviews WHERE product_id = %s AND buyer_id = %s", (product_id, user["id"]))
    if cur.rowcount == 0:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Bạn chưa đánh giá sản phẩm này.")
