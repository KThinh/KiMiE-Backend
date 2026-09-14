"""Giỏ hàng lưu theo tài khoản (bảng cart_items) — sẵn sàng để nâng cấp lên giỏ
hàng đồng bộ nhiều thiết bị. Frontend hiện tại vẫn ưu tiên giỏ hàng cục bộ
(localStorage) cho khách chưa đăng nhập; API này phục vụ khi đã đăng nhập."""

import sqlite3

from fastapi import APIRouter, Depends, HTTPException, status

from app.database import get_db
from app.deps import get_current_user
from app.schemas import CartItemIn, CartOut, CartItemOut
from app.serializers import row_to_product

router = APIRouter(prefix="/api/cart", tags=["cart"])


def _load_cart(db: sqlite3.Connection, buyer_id: int) -> CartOut:
    rows = db.execute(
        """SELECT ci.id AS cart_id, ci.quantity,
                   p.id, p.seller_id, p.name, p.description, p.price, p.stock, p.sold_count,
                   p.rating, p.image_url, p.status, p.created_at, p.updated_at,
                   v.code AS village_code, v.name AS village_name,
                   COALESCE(sp.shop_name, u.name) AS shop_name
            FROM cart_items ci
            JOIN products p ON p.id = ci.product_id
            JOIN villages v ON v.id = p.village_id
            JOIN users u ON u.id = p.seller_id
            LEFT JOIN seller_profiles sp ON sp.user_id = p.seller_id
            WHERE ci.buyer_id = ?
            ORDER BY ci.added_at""",
        (buyer_id,),
    ).fetchall()

    items = []
    subtotal = 0.0
    for r in rows:
        product = row_to_product(r)
        line_total = product.price * r["quantity"]
        subtotal += line_total
        items.append(CartItemOut(id=r["cart_id"], product=product, quantity=r["quantity"], line_total=line_total))
    return CartOut(items=items, subtotal=subtotal)


@router.get("", response_model=CartOut)
def get_cart(user: sqlite3.Row = Depends(get_current_user), db: sqlite3.Connection = Depends(get_db)):
    return _load_cart(db, user["id"])


@router.post("", response_model=CartOut, status_code=status.HTTP_201_CREATED)
def add_to_cart(payload: CartItemIn, user: sqlite3.Row = Depends(get_current_user), db: sqlite3.Connection = Depends(get_db)):
    product = db.execute("SELECT id FROM products WHERE id = ? AND status = 'active'", (payload.product_id,)).fetchone()
    if product is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy sản phẩm.")
    existing = db.execute(
        "SELECT id, quantity FROM cart_items WHERE buyer_id = ? AND product_id = ?", (user["id"], payload.product_id)
    ).fetchone()
    if existing:
        db.execute("UPDATE cart_items SET quantity = quantity + ? WHERE id = ?", (payload.quantity, existing["id"]))
    else:
        db.execute(
            "INSERT INTO cart_items (buyer_id, product_id, quantity) VALUES (?, ?, ?)",
            (user["id"], payload.product_id, payload.quantity),
        )
    return _load_cart(db, user["id"])


@router.put("/{product_id}", response_model=CartOut)
def set_quantity(product_id: int, payload: CartItemIn, user: sqlite3.Row = Depends(get_current_user), db: sqlite3.Connection = Depends(get_db)):
    row = db.execute("SELECT id FROM cart_items WHERE buyer_id = ? AND product_id = ?", (user["id"], product_id)).fetchone()
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Sản phẩm này chưa có trong giỏ hàng.")
    db.execute("UPDATE cart_items SET quantity = ? WHERE id = ?", (payload.quantity, row["id"]))
    return _load_cart(db, user["id"])


@router.delete("/{product_id}", response_model=CartOut)
def remove_from_cart(product_id: int, user: sqlite3.Row = Depends(get_current_user), db: sqlite3.Connection = Depends(get_db)):
    db.execute("DELETE FROM cart_items WHERE buyer_id = ? AND product_id = ?", (user["id"], product_id))
    return _load_cart(db, user["id"])
