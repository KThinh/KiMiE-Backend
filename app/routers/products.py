import psycopg

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.database import get_db
from app.deps import require_seller
from app.schemas import ProductIn, ProductListOut, ProductOut, ProductUpdateIn
from app.serializers import PRODUCT_SELECT, row_to_product

router = APIRouter(prefix="/api/products", tags=["products"])


def _village_id(db: psycopg.Connection, code: str) -> int:
    row = db.execute("SELECT id FROM villages WHERE code = %s", (code,)).fetchone()
    if row is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Làng nghề '{code}' không hợp lệ.")
    return row["id"]


@router.get("", response_model=ProductListOut)
def list_products(
    village: str | None = Query(default=None, description="Lọc theo mã làng nghề: bt/vp/pv"),
    q: str | None = Query(default=None, description="Tìm theo tên sản phẩm"),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=12, ge=1, le=100),
    db: psycopg.Connection = Depends(get_db),
):
    where = ["p.status = 'active'"]
    params: list = []
    if village:
        where.append("v.code = %s")
        params.append(village)
    if q:
        # ILIKE (không phân biệt hoa/thường) để khớp hành vi LIKE mặc định của SQLite trước đây
        where.append("p.name ILIKE %s")
        params.append(f"%{q}%")
    where_sql = " AND ".join(where)

    total = db.execute(
        f"SELECT COUNT(*) FROM products p JOIN villages v ON v.id = p.village_id WHERE {where_sql}", params
    ).fetchone()["count"]

    rows = db.execute(
        f"{PRODUCT_SELECT} WHERE {where_sql} ORDER BY p.created_at DESC LIMIT %s OFFSET %s",
        [*params, per_page, (page - 1) * per_page],
    ).fetchall()

    return ProductListOut(total=total, page=page, per_page=per_page, items=[row_to_product(r) for r in rows])


@router.get("/{product_id}", response_model=ProductOut)
def get_product(product_id: int, db: psycopg.Connection = Depends(get_db)):
    row = db.execute(f"{PRODUCT_SELECT} WHERE p.id = %s", (product_id,)).fetchone()
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy sản phẩm.")
    return row_to_product(row)


@router.post("", response_model=ProductOut, status_code=status.HTTP_201_CREATED)
def create_product(
    payload: ProductIn,
    seller: dict = Depends(require_seller),
    db: psycopg.Connection = Depends(get_db),
):
    village_id = _village_id(db, payload.village_code)
    cur = db.execute(
        """INSERT INTO products (seller_id, village_id, name, description, price, stock, image_url)
           VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id""",
        (seller["id"], village_id, payload.name, payload.description, payload.price, payload.stock, payload.image_url),
    )
    new_id = cur.fetchone()["id"]
    row = db.execute(f"{PRODUCT_SELECT} WHERE p.id = %s", (new_id,)).fetchone()
    return row_to_product(row)


def _owned_product(db: psycopg.Connection, product_id: int, seller_id: int) -> dict:
    row = db.execute("SELECT * FROM products WHERE id = %s", (product_id,)).fetchone()
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy sản phẩm.")
    if row["seller_id"] != seller_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Bạn không có quyền sửa sản phẩm của người bán khác.")
    return row


@router.put("/{product_id}", response_model=ProductOut)
def update_product(
    product_id: int,
    payload: ProductUpdateIn,
    seller: dict = Depends(require_seller),
    db: psycopg.Connection = Depends(get_db),
):
    existing = _owned_product(db, product_id, seller["id"])
    village_id = _village_id(db, payload.village_code) if payload.village_code else existing["village_id"]
    if payload.status is not None and payload.status not in ("active", "hidden"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "status phải là 'active' hoặc 'hidden'.")

    db.execute(
        """UPDATE products SET
               name = %s, village_id = %s, price = %s, stock = %s, description = %s,
               image_url = %s, status = %s, updated_at = CURRENT_TIMESTAMP
           WHERE id = %s""",
        (
            payload.name if payload.name is not None else existing["name"],
            village_id,
            payload.price if payload.price is not None else existing["price"],
            payload.stock if payload.stock is not None else existing["stock"],
            payload.description if payload.description is not None else existing["description"],
            payload.image_url if payload.image_url is not None else existing["image_url"],
            payload.status if payload.status is not None else existing["status"],
            product_id,
        ),
    )
    row = db.execute(f"{PRODUCT_SELECT} WHERE p.id = %s", (product_id,)).fetchone()
    return row_to_product(row)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(
    product_id: int,
    seller: dict = Depends(require_seller),
    db: psycopg.Connection = Depends(get_db),
):
    _owned_product(db, product_id, seller["id"])
    try:
        db.execute("DELETE FROM products WHERE id = %s", (product_id,))
    except psycopg.IntegrityError:
        # sản phẩm đã nằm trong giỏ hàng/đơn hàng của ai đó — FK chặn xoá để giữ lịch sử đơn hàng
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Không thể xoá sản phẩm đã từng được đặt hàng hoặc đang trong giỏ hàng — "
            "hãy cập nhật status = 'hidden' để ẩn khỏi Sàn thương mại thay vì xoá.",
        )
