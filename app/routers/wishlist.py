import psycopg

from fastapi import APIRouter, Depends, HTTPException, status

from app.database import get_db
from app.deps import get_current_user
from app.schemas import CartOut, WishlistIn, WishlistItemOut
from app.serializers import PRODUCT_SELECT, row_to_product

router = APIRouter(prefix="/api/wishlist", tags=["wishlist"])


@router.get("", response_model=list[WishlistItemOut])
def list_wishlist(user: dict = Depends(get_current_user), db: psycopg.Connection = Depends(get_db)):
    rows = db.execute(
        f"""SELECT wi.id AS wishlist_id, wi.added_at, sub.*
            FROM wishlist_items wi
            JOIN ({PRODUCT_SELECT}) sub ON sub.id = wi.product_id
            WHERE wi.buyer_id = %s
            ORDER BY wi.added_at DESC""",
        (user["id"],),
    ).fetchall()
    return [WishlistItemOut(id=r["wishlist_id"], product=row_to_product(r), added_at=r["added_at"]) for r in rows]


@router.post("", status_code=status.HTTP_201_CREATED)
def add_to_wishlist(payload: WishlistIn, user: dict = Depends(get_current_user), db: psycopg.Connection = Depends(get_db)):
    product = db.execute("SELECT id FROM products WHERE id = %s", (payload.product_id,)).fetchone()
    if product is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy sản phẩm.")
    db.execute(
        "INSERT INTO wishlist_items (buyer_id, product_id) VALUES (%s, %s) ON CONFLICT (buyer_id, product_id) DO NOTHING",
        (user["id"], payload.product_id),
    )
    return {"ok": True}


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_from_wishlist(product_id: int, user: dict = Depends(get_current_user), db: psycopg.Connection = Depends(get_db)):
    db.execute("DELETE FROM wishlist_items WHERE buyer_id = %s AND product_id = %s", (user["id"], product_id))


@router.post("/{product_id}/move-to-cart", response_model=CartOut)
def move_to_cart(product_id: int, user: dict = Depends(get_current_user), db: psycopg.Connection = Depends(get_db)):
    from app.routers.cart import _load_cart  # tránh import vòng ở module-level

    product = db.execute("SELECT id FROM products WHERE id = %s AND status = 'active'", (product_id,)).fetchone()
    if product is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Sản phẩm không còn bán.")
    existing = db.execute(
        "SELECT id, quantity FROM cart_items WHERE buyer_id = %s AND product_id = %s AND color IS NULL AND size IS NULL",
        (user["id"], product_id),
    ).fetchone()
    if existing:
        db.execute("UPDATE cart_items SET quantity = quantity + 1 WHERE id = %s", (existing["id"],))
    else:
        db.execute("INSERT INTO cart_items (buyer_id, product_id, quantity) VALUES (%s, %s, 1)", (user["id"], product_id))
    db.execute("DELETE FROM wishlist_items WHERE buyer_id = %s AND product_id = %s", (user["id"], product_id))
    return _load_cart(db, user["id"])
