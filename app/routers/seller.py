import psycopg

from fastapi import APIRouter, Depends, HTTPException, status

from app.database import get_db
from app.deps import get_current_user, require_seller
from app.schemas import ProductOut, SellerOrderItemOut, SellerRegisterIn, SellerStatsOut, SellerTransactionOut, UserOut
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

    existing = db.execute("SELECT id, payment_qr_url FROM seller_profiles WHERE user_id = %s", (user["id"],)).fetchone()
    qr = payload.payment_qr_url if payload.payment_qr_url is not None else (existing["payment_qr_url"] if existing else None)
    if existing is not None:
        db.execute(
            "UPDATE seller_profiles SET shop_name = %s, village_id = %s, phone = %s, bio = %s, payment_qr_url = %s WHERE user_id = %s",
            (payload.shop_name, village["id"], payload.phone, payload.bio, qr, user["id"]),
        )
    else:
        db.execute(
            "INSERT INTO seller_profiles (user_id, shop_name, village_id, phone, bio, payment_qr_url) VALUES (%s, %s, %s, %s, %s, %s)",
            (user["id"], payload.shop_name, village["id"], payload.phone, payload.bio, qr),
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


@router.get("/orders", response_model=list[SellerOrderItemOut])
def my_seller_orders(seller: dict = Depends(require_seller), db: psycopg.Connection = Depends(get_db)):
    """Các dòng order_items thuộc gian hàng của seller — để cập nhật trạng thái vận chuyển."""
    rows = db.execute(
        """SELECT oi.id AS item_id, oi.order_id, oi.product_id, p.name AS product_name, p.image_url AS product_image,
                  oi.quantity, oi.color, oi.size, oi.price_at_purchase, oi.item_status,
                  o.status AS order_status, o.recipient_name, o.shipping_address, o.created_at
           FROM order_items oi
           JOIN products p ON p.id = oi.product_id
           JOIN orders o ON o.id = oi.order_id
           WHERE oi.seller_id = %s
           ORDER BY oi.order_id DESC""",
        (seller["id"],),
    ).fetchall()
    return [SellerOrderItemOut(**dict(r)) for r in rows]


@router.get("/transactions", response_model=list[SellerTransactionOut])
def my_transactions(
    payment_status: str | None = None,
    seller: dict = Depends(require_seller),
    db: psycopg.Connection = Depends(get_db),
):
    where = "op.seller_id = %s"
    params: list = [seller["id"]]
    if payment_status:
        where += " AND op.status = %s"
        params.append(payment_status)
    rows = db.execute(
        f"""SELECT op.id AS payment_id, op.order_id, o.buyer_id, u.name AS buyer_name,
                   op.amount, op.qr_image_url, op.buyer_confirmed_at, op.seller_confirmed_at,
                   op.status, op.created_at
            FROM order_payments op
            JOIN orders o ON o.id = op.order_id
            JOIN users u ON u.id = o.buyer_id
            WHERE {where}
            ORDER BY op.created_at DESC""",
        params,
    ).fetchall()
    return [SellerTransactionOut(**dict(r)) for r in rows]


@router.post("/transactions/confirm-all")
def confirm_all_transactions(seller: dict = Depends(require_seller), db: psycopg.Connection = Depends(get_db)):
    from app.routers.orders import _recompute_order_status, _try_complete_payment  # tránh import vòng

    pending = db.execute(
        "SELECT * FROM order_payments WHERE seller_id = %s AND status = 'pending'", (seller["id"],)
    ).fetchall()
    confirmed = 0
    for payment in pending:
        db.execute(
            "UPDATE order_payments SET seller_confirmed_at = CURRENT_TIMESTAMP WHERE id = %s AND seller_confirmed_at IS NULL",
            (payment["id"],),
        )
        fresh = db.execute("SELECT * FROM order_payments WHERE id = %s", (payment["id"],)).fetchone()
        _try_complete_payment(db, fresh)
        _recompute_order_status(db, fresh["order_id"])
        confirmed += 1
    return {"confirmed": confirmed}
