"""Giỏ hàng lưu theo tài khoản (bảng cart_items) — sẵn sàng để nâng cấp lên giỏ
hàng đồng bộ nhiều thiết bị. Frontend hiện tại vẫn ưu tiên giỏ hàng cục bộ
(localStorage) cho khách chưa đăng nhập; API này phục vụ khi đã đăng nhập.

Mỗi dòng giỏ hàng giờ có thêm màu/size đã chọn — 2 dòng cùng sản phẩm nhưng khác
màu/size là 2 dòng riêng biệt (UNIQUE(buyer_id, product_id, color, size))."""

import psycopg

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.database import get_db
from app.deps import get_current_user
from app.schemas import CartItemIn, CartOut, CartItemOut
from app.serializers import PRODUCT_SELECT, row_to_product

router = APIRouter(prefix="/api/cart", tags=["cart"])


def _load_cart(db: psycopg.Connection, buyer_id: int) -> CartOut:
    rows = db.execute(
        f"""SELECT ci.id AS cart_id, ci.quantity, ci.color AS cart_color, ci.size AS cart_size, sub.*
            FROM cart_items ci
            JOIN ({PRODUCT_SELECT}) sub ON sub.id = ci.product_id
            WHERE ci.buyer_id = %s
            ORDER BY ci.added_at""",
        (buyer_id,),
    ).fetchall()

    items = []
    subtotal = 0.0
    for r in rows:
        product = row_to_product(r)
        line_total = product.price * r["quantity"]
        subtotal += line_total
        items.append(CartItemOut(
            id=r["cart_id"], product=product, quantity=r["quantity"],
            color=r["cart_color"], size=r["cart_size"], line_total=line_total,
        ))
    return CartOut(items=items, subtotal=subtotal)


@router.get("", response_model=CartOut)
def get_cart(user: dict = Depends(get_current_user), db: psycopg.Connection = Depends(get_db)):
    return _load_cart(db, user["id"])


@router.post("", response_model=CartOut, status_code=status.HTTP_201_CREATED)
def add_to_cart(payload: CartItemIn, user: dict = Depends(get_current_user), db: psycopg.Connection = Depends(get_db)):
    product = db.execute("SELECT id FROM products WHERE id = %s AND status = 'active'", (payload.product_id,)).fetchone()
    if product is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy sản phẩm.")
    existing = db.execute(
        """SELECT id, quantity FROM cart_items
           WHERE buyer_id = %s AND product_id = %s AND color IS NOT DISTINCT FROM %s AND size IS NOT DISTINCT FROM %s""",
        (user["id"], payload.product_id, payload.color, payload.size),
    ).fetchone()
    if existing:
        db.execute("UPDATE cart_items SET quantity = quantity + %s WHERE id = %s", (payload.quantity, existing["id"]))
    else:
        db.execute(
            "INSERT INTO cart_items (buyer_id, product_id, quantity, color, size) VALUES (%s, %s, %s, %s, %s)",
            (user["id"], payload.product_id, payload.quantity, payload.color, payload.size),
        )
    return _load_cart(db, user["id"])


@router.put("/{product_id}", response_model=CartOut)
def set_quantity(product_id: int, payload: CartItemIn, user: dict = Depends(get_current_user), db: psycopg.Connection = Depends(get_db)):
    row = db.execute(
        """SELECT id FROM cart_items
           WHERE buyer_id = %s AND product_id = %s AND color IS NOT DISTINCT FROM %s AND size IS NOT DISTINCT FROM %s""",
        (user["id"], product_id, payload.color, payload.size),
    ).fetchone()
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Sản phẩm này chưa có trong giỏ hàng.")
    db.execute("UPDATE cart_items SET quantity = %s WHERE id = %s", (payload.quantity, row["id"]))
    return _load_cart(db, user["id"])


@router.delete("/{product_id}", response_model=CartOut)
def remove_from_cart(
    product_id: int,
    color: str | None = Query(default=None),
    size: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: psycopg.Connection = Depends(get_db),
):
    db.execute(
        "DELETE FROM cart_items WHERE buyer_id = %s AND product_id = %s AND color IS NOT DISTINCT FROM %s AND size IS NOT DISTINCT FROM %s",
        (user["id"], product_id, color, size),
    )
    return _load_cart(db, user["id"])


@router.post("/{cart_item_id}/save-for-later", response_model=CartOut)
def save_for_later(cart_item_id: int, user: dict = Depends(get_current_user), db: psycopg.Connection = Depends(get_db)):
    row = db.execute(
        "SELECT product_id FROM cart_items WHERE id = %s AND buyer_id = %s", (cart_item_id, user["id"])
    ).fetchone()
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy dòng giỏ hàng này.")
    db.execute(
        "INSERT INTO wishlist_items (buyer_id, product_id) VALUES (%s, %s) ON CONFLICT (buyer_id, product_id) DO NOTHING",
        (user["id"], row["product_id"]),
    )
    db.execute("DELETE FROM cart_items WHERE id = %s", (cart_item_id,))
    return _load_cart(db, user["id"])
