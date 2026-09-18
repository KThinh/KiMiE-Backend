import psycopg

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.database import get_db
from app.deps import require_seller
from app.schemas import ProductIn, ProductListOut, ProductOut, ProductUpdateIn
from app.serializers import PRODUCT_SELECT, row_to_product

router = APIRouter(prefix="/api/products", tags=["products"])

_SORTS = {
    "newest": "p.created_at DESC",
    "price_asc": "p.price ASC",
    "price_desc": "p.price DESC",
    "rating": "p.rating DESC, p.review_count DESC",
    "best_selling": "p.sold_count DESC",
    "featured": "p.sold_count DESC, p.rating DESC",
}


def _village_id(db: psycopg.Connection, code: str) -> int:
    row = db.execute("SELECT id FROM villages WHERE code = %s", (code,)).fetchone()
    if row is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Làng nghề '{code}' không hợp lệ.")
    return row["id"]


def _set_images(db: psycopg.Connection, product_id: int, images: list[str]) -> None:
    db.execute("DELETE FROM product_images WHERE product_id = %s", (product_id,))
    for i, url in enumerate(images):
        db.execute(
            "INSERT INTO product_images (product_id, image_url, sort_order) VALUES (%s, %s, %s)",
            (product_id, url, i),
        )


@router.get("", response_model=ProductListOut)
def list_products(
    village: str | None = Query(default=None, description="Lọc theo mã làng nghề: bt/vp/pv"),
    q: str | None = Query(default=None, description="Tìm theo tên/mô tả sản phẩm"),
    color: str | None = Query(default=None, description="Lọc theo màu"),
    size: str | None = Query(default=None, description="Lọc theo size"),
    min_price: float | None = Query(default=None, ge=0),
    max_price: float | None = Query(default=None, ge=0),
    sale_only: bool = Query(default=False, description="Chỉ sản phẩm đang giảm giá"),
    new_only: bool = Query(default=False, description="Chỉ sản phẩm mới (14 ngày gần đây)"),
    sort: str = Query(default="featured", description="featured|newest|price_asc|price_desc|rating|best_selling"),
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
        where.append("(p.name ILIKE %s OR p.description ILIKE %s)")
        params += [f"%{q}%", f"%{q}%"]
    if color:
        where.append("p.colors ILIKE %s")
        params.append(f"%{color}%")
    if size:
        where.append("p.sizes ILIKE %s")
        params.append(f"%{size}%")
    if min_price is not None:
        where.append("p.price >= %s")
        params.append(min_price)
    if max_price is not None:
        where.append("p.price <= %s")
        params.append(max_price)
    if sale_only:
        where.append("p.original_price IS NOT NULL AND p.original_price > p.price")
    if new_only:
        where.append("p.created_at > NOW() - INTERVAL '14 days'")
    where_sql = " AND ".join(where)
    order_sql = _SORTS.get(sort, _SORTS["featured"])

    total = db.execute(
        f"SELECT COUNT(*) FROM products p JOIN villages v ON v.id = p.village_id WHERE {where_sql}", params
    ).fetchone()["count"]

    rows = db.execute(
        f"{PRODUCT_SELECT} WHERE {where_sql} ORDER BY {order_sql} LIMIT %s OFFSET %s",
        [*params, per_page, (page - 1) * per_page],
    ).fetchall()

    return ProductListOut(total=total, page=page, per_page=per_page, items=[row_to_product(r) for r in rows])


@router.get("/{product_id}", response_model=ProductOut)
def get_product(product_id: int, db: psycopg.Connection = Depends(get_db)):
    row = db.execute(f"{PRODUCT_SELECT} WHERE p.id = %s", (product_id,)).fetchone()
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy sản phẩm.")
    return row_to_product(row)


@router.get("/{product_id}/related", response_model=list[ProductOut])
def related_products(
    product_id: int,
    limit: int = Query(default=4, ge=1, le=12),
    db: psycopg.Connection = Depends(get_db),
):
    base = db.execute("SELECT village_id, seller_id FROM products WHERE id = %s", (product_id,)).fetchone()
    if base is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy sản phẩm.")
    rows = db.execute(
        f"""{PRODUCT_SELECT}
            WHERE p.id != %s AND p.status = 'active' AND (p.village_id = %s OR p.seller_id = %s)
            ORDER BY p.sold_count DESC LIMIT %s""",
        (product_id, base["village_id"], base["seller_id"], limit),
    ).fetchall()
    return [row_to_product(r) for r in rows]


@router.post("", response_model=ProductOut, status_code=status.HTTP_201_CREATED)
def create_product(
    payload: ProductIn,
    seller: dict = Depends(require_seller),
    db: psycopg.Connection = Depends(get_db),
):
    village_id = _village_id(db, payload.village_code)
    cur = db.execute(
        """INSERT INTO products
               (seller_id, village_id, name, description, material, size_guide, colors, sizes,
                price, original_price, stock, image_url)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id""",
        (
            seller["id"], village_id, payload.name, payload.description, payload.material, payload.size_guide,
            payload.colors, payload.sizes, payload.price, payload.original_price, payload.stock, payload.image_url,
        ),
    )
    new_id = cur.fetchone()["id"]
    if payload.images:
        _set_images(db, new_id, payload.images)
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
               name = %s, village_id = %s, price = %s, original_price = %s, stock = %s,
               description = %s, material = %s, size_guide = %s, colors = %s, sizes = %s,
               image_url = %s, status = %s, updated_at = CURRENT_TIMESTAMP
           WHERE id = %s""",
        (
            payload.name if payload.name is not None else existing["name"],
            village_id,
            payload.price if payload.price is not None else existing["price"],
            payload.original_price if payload.original_price is not None else existing["original_price"],
            payload.stock if payload.stock is not None else existing["stock"],
            payload.description if payload.description is not None else existing["description"],
            payload.material if payload.material is not None else existing["material"],
            payload.size_guide if payload.size_guide is not None else existing["size_guide"],
            payload.colors if payload.colors is not None else existing["colors"],
            payload.sizes if payload.sizes is not None else existing["sizes"],
            payload.image_url if payload.image_url is not None else existing["image_url"],
            payload.status if payload.status is not None else existing["status"],
            product_id,
        ),
    )
    if payload.images is not None:
        _set_images(db, product_id, payload.images)
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
        db.execute("DELETE FROM product_images WHERE product_id = %s", (product_id,))
        db.execute("DELETE FROM products WHERE id = %s", (product_id,))
    except psycopg.IntegrityError:
        # sản phẩm đã nằm trong giỏ hàng/đơn hàng của ai đó — FK chặn xoá để giữ lịch sử đơn hàng
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Không thể xoá sản phẩm đã từng được đặt hàng hoặc đang trong giỏ hàng — "
            "hãy cập nhật status = 'hidden' để ẩn khỏi Sàn thương mại thay vì xoá.",
        )
