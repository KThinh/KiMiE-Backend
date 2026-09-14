import psycopg

from fastapi import APIRouter, Depends, HTTPException, status

from app.database import get_db
from app.deps import get_current_user, require_seller
from app.schemas import ProductOut, SellerRegisterIn, SellerStatsOut, UserOut
from app.serializers import PRODUCT_SELECT, row_to_product, row_to_user

router = APIRouter(prefix="/api/seller", tags=["seller"])


@router.post("/register", response_model=UserOut)
def register_seller(
    payload: SellerRegisterIn,
    user: dict = Depends(get_current_user),
    db: psycopg.Connection = Depends(get_db),
):
    village = db.execute("SELECT id FROM villages WHERE code = %s", (payload.village_code,)).fetchone()
    if village is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Làng nghề '{payload.village_code}' không hợp lệ.")

    existing = db.execute("SELECT id FROM seller_profiles WHERE user_id = %s", (user["id"],)).fetchone()
    if existing is not None:
        db.execute(
            "UPDATE seller_profiles SET shop_name = %s, village_id = %s, phone = %s, bio = %s WHERE user_id = %s",
            (payload.shop_name, village["id"], payload.phone, payload.bio, user["id"]),
        )
    else:
        db.execute(
            "INSERT INTO seller_profiles (user_id, shop_name, village_id, phone, bio) VALUES (%s, %s, %s, %s, %s)",
            (user["id"], payload.shop_name, village["id"], payload.phone, payload.bio),
        )
    db.execute("UPDATE users SET is_seller = 1 WHERE id = %s", (user["id"],))

    fresh_user = db.execute("SELECT * FROM users WHERE id = %s", (user["id"],)).fetchone()
    return row_to_user(db, fresh_user)


@router.get("/products", response_model=list[ProductOut])
def my_products(seller: dict = Depends(require_seller), db: psycopg.Connection = Depends(get_db)):
    rows = db.execute(f"{PRODUCT_SELECT} WHERE p.seller_id = %s ORDER BY p.created_at DESC", (seller["id"],)).fetchall()
    return [row_to_product(r) for r in rows]


@router.get("/stats", response_model=SellerStatsOut)
def my_stats(seller: dict = Depends(require_seller), db: psycopg.Connection = Depends(get_db)):
    row = db.execute(
        """SELECT
               COUNT(*) AS total_products,
               COALESCE(SUM(CASE WHEN stock > 0 THEN 1 ELSE 0 END), 0) AS in_stock,
               COALESCE(SUM(CASE WHEN stock = 0 THEN 1 ELSE 0 END), 0) AS out_of_stock,
               COALESCE(SUM(price * stock), 0) AS inventory_value,
               COALESCE(SUM(sold_count), 0) AS total_sold,
               COALESCE(SUM(price * sold_count), 0) AS total_revenue
           FROM products WHERE seller_id = %s""",
        (seller["id"],),
    ).fetchone()
    return SellerStatsOut(**dict(row))
