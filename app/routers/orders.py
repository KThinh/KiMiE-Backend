"""Đơn hàng + thanh toán theo từng người bán (mỗi seller có mã QR riêng).

Khi tạo đơn, các dòng giỏ hàng được nhóm theo seller_id: mỗi seller xuất hiện
trong đơn có đúng 1 dòng trong order_payments (chụp lại QR + số tiền phải trả
cho seller đó tại thời điểm đặt hàng). Giao dịch với 1 seller chỉ "hoàn tất"
khi CẢ buyer (đã chuyển khoản) và seller (đã nhận được tiền) cùng xác nhận —
lúc đó trigger DB mới trừ tồn kho/cộng đã bán cho đúng các dòng hàng của seller
đó trong đơn. Nếu 1 trong 2 bên báo thất bại, giao dịch failed, đơn bị huỷ,
không có gì bị trừ tồn kho vì chưa từng completed.

orders.status là suy ra (không cho sửa tay) từ: trạng thái các order_payments
+ item_status của order_items — xem _recompute_order_status()."""

import psycopg

from fastapi import APIRouter, Depends, HTTPException, status

from app.database import get_db
from app.deps import get_current_user, require_seller
from app.notify import notify
from app.schemas import ItemStatusIn, OrderCreateIn, OrderItemOut, OrderOut, OrderPaymentOut

router = APIRouter(prefix="/api/orders", tags=["orders"])

# khớp đúng VOUCHERS trong script.js (frontend) — 1 mã / hoá đơn
VOUCHERS = {
    "GIULUA10": {"type": "pct", "val": 10},
    "TINHHOA15": {"type": "pct", "val": 15},
    "FREESHIP": {"type": "amt", "val": 30_000},
}

SHIPPING_FEES = {"standard": 20_000, "express": 45_000}
ITEM_STAGES = ["processing", "shipped", "delivered"]


def _discount_of(code: str | None, subtotal: float) -> float:
    if not code:
        return 0
    v = VOUCHERS.get(code)
    if v is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Mã voucher '{code}' không hợp lệ.")
    if v["type"] == "pct":
        return min(subtotal, round(subtotal * v["val"] / 100))
    return min(subtotal, v["val"])


def _row_to_order(db: psycopg.Connection, order: dict) -> OrderOut:
    items = db.execute(
        """SELECT oi.id, oi.product_id, p.name AS product_name, p.image_url AS product_image,
                  oi.seller_id, oi.quantity, oi.color, oi.size, oi.price_at_purchase, oi.item_status
           FROM order_items oi JOIN products p ON p.id = oi.product_id
           WHERE oi.order_id = %s ORDER BY oi.id""",
        (order["id"],),
    ).fetchall()
    payments = db.execute(
        """SELECT op.seller_id, COALESCE(sp.shop_name, u.name) AS shop_name, op.amount, op.qr_image_url,
                  op.buyer_confirmed_at, op.seller_confirmed_at, op.status
           FROM order_payments op
           JOIN users u ON u.id = op.seller_id
           LEFT JOIN seller_profiles sp ON sp.user_id = op.seller_id
           WHERE op.order_id = %s ORDER BY op.seller_id""",
        (order["id"],),
    ).fetchall()
    return OrderOut(
        id=order["id"],
        status=order["status"],
        voucher_code=order["voucher_code"],
        discount_amount=order["discount_amount"],
        shipping_method=order["shipping_method"],
        shipping_fee=order["shipping_fee"],
        total_price=order["total_price"],
        recipient_name=order["recipient_name"],
        recipient_email=order["recipient_email"],
        recipient_phone=order["recipient_phone"],
        shipping_address=order["shipping_address"],
        created_at=order["created_at"],
        items=[OrderItemOut(**dict(i)) for i in items],
        payments=[OrderPaymentOut(**dict(p)) for p in payments],
    )


@router.post("", response_model=OrderOut, status_code=status.HTTP_201_CREATED)
def create_order(
    payload: OrderCreateIn,
    user: dict = Depends(get_current_user),
    db: psycopg.Connection = Depends(get_db),
):
    if payload.shipping_method not in SHIPPING_FEES:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Phương thức vận chuyển không hợp lệ.")

    subtotal = 0.0
    resolved = []  # (product_row, quantity, color, size)
    for item in payload.items:
        product = db.execute("SELECT * FROM products WHERE id = %s", (item.product_id,)).fetchone()
        if product is None or product["status"] != "active":
            raise HTTPException(status.HTTP_404_NOT_FOUND, f"Sản phẩm #{item.product_id} không còn bán.")
        if product["stock"] < item.quantity:
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                f"'{product['name']}' chỉ còn {product['stock']} sản phẩm, không đủ số lượng bạn đặt.",
            )
        subtotal += product["price"] * item.quantity
        resolved.append((product, item.quantity, item.color, item.size))

    discount = _discount_of(payload.voucher_code, subtotal)
    shipping_fee = SHIPPING_FEES[payload.shipping_method]
    total = subtotal - discount + shipping_fee

    cur = db.execute(
        """INSERT INTO orders
               (buyer_id, recipient_name, recipient_email, recipient_phone, shipping_address,
                shipping_method, shipping_fee, voucher_code, discount_amount, total_price, status)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'pending') RETURNING id""",
        (
            user["id"], payload.recipient_name, payload.recipient_email, payload.recipient_phone,
            payload.shipping_address, payload.shipping_method, shipping_fee,
            payload.voucher_code, discount, total,
        ),
    )
    order_id = cur.fetchone()["id"]

    by_seller: dict[int, float] = {}
    for product, qty, color, size in resolved:
        db.execute(
            """INSERT INTO order_items (order_id, product_id, seller_id, quantity, color, size, price_at_purchase)
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (order_id, product["id"], product["seller_id"], qty, color, size, product["price"]),
        )
        by_seller[product["seller_id"]] = by_seller.get(product["seller_id"], 0.0) + product["price"] * qty

    for seller_id, amount in by_seller.items():
        sp = db.execute("SELECT payment_qr_url FROM seller_profiles WHERE user_id = %s", (seller_id,)).fetchone()
        db.execute(
            "INSERT INTO order_payments (order_id, seller_id, amount, qr_image_url) VALUES (%s, %s, %s, %s)",
            (order_id, seller_id, amount, sp["payment_qr_url"] if sp else None),
        )
        notify(
            db, seller_id, "new_order", "Bạn có đơn hàng mới",
            f"Đơn hàng #{order_id} vừa được đặt — vui lòng chuẩn bị hàng và kiểm tra thanh toán.",
            order_id=order_id,
        )

    order = db.execute("SELECT * FROM orders WHERE id = %s", (order_id,)).fetchone()
    return _row_to_order(db, order)


def _owned_order(db: psycopg.Connection, order_id: int, buyer_id: int) -> dict:
    order = db.execute("SELECT * FROM orders WHERE id = %s", (order_id,)).fetchone()
    if order is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy đơn hàng.")
    if order["buyer_id"] != buyer_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Đây không phải đơn hàng của bạn.")
    return order


def _get_payment(db: psycopg.Connection, order_id: int, seller_id: int) -> dict:
    row = db.execute(
        "SELECT * FROM order_payments WHERE order_id = %s AND seller_id = %s", (order_id, seller_id)
    ).fetchone()
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy giao dịch thanh toán này.")
    return row


def _recompute_order_status(db: psycopg.Connection, order_id: int) -> None:
    payments = db.execute("SELECT status FROM order_payments WHERE order_id = %s", (order_id,)).fetchall()
    if any(p["status"] == "failed" for p in payments):
        new_status = "cancelled"
    elif not all(p["status"] == "completed" for p in payments):
        new_status = "pending"
    else:
        items = db.execute("SELECT item_status FROM order_items WHERE order_id = %s", (order_id,)).fetchall()
        stages = [ITEM_STAGES.index(i["item_status"]) for i in items]
        new_status = ITEM_STAGES[min(stages)] if stages else "processing"
    db.execute("UPDATE orders SET status = %s WHERE id = %s", (new_status, order_id))


def _try_complete_payment(db: psycopg.Connection, payment: dict) -> None:
    """Nếu cả 2 bên đã xác nhận, chốt giao dịch — trigger DB sẽ tự trừ tồn kho/cộng đã bán."""
    if payment["buyer_confirmed_at"] is not None and payment["seller_confirmed_at"] is not None:
        db.execute(
            "UPDATE order_payments SET status = 'completed' WHERE id = %s AND status = 'pending'",
            (payment["id"],),
        )


@router.post("/{order_id}/payments/{seller_id}/buyer-confirm", response_model=OrderOut)
def buyer_confirm_payment(
    order_id: int, seller_id: int,
    user: dict = Depends(get_current_user),
    db: psycopg.Connection = Depends(get_db),
):
    _owned_order(db, order_id, user["id"])
    payment = _get_payment(db, order_id, seller_id)
    if payment["status"] != "pending":
        raise HTTPException(status.HTTP_409_CONFLICT, f"Giao dịch này đang ở trạng thái '{payment['status']}'.")
    db.execute("UPDATE order_payments SET buyer_confirmed_at = CURRENT_TIMESTAMP WHERE id = %s", (payment["id"],))
    payment = _get_payment(db, order_id, seller_id)
    _try_complete_payment(db, payment)
    _recompute_order_status(db, order_id)
    if payment["status"] != "completed":
        notify(db, seller_id, "buyer_paid", "Người mua báo đã chuyển khoản",
               f"Người mua đã xác nhận chuyển khoản cho đơn #{order_id} — vui lòng kiểm tra và xác nhận đã nhận tiền.",
               order_id=order_id)
    order = db.execute("SELECT * FROM orders WHERE id = %s", (order_id,)).fetchone()
    return _row_to_order(db, order)


@router.post("/{order_id}/payments/{seller_id}/seller-confirm", response_model=OrderOut)
def seller_confirm_payment(
    order_id: int, seller_id: int,
    seller: dict = Depends(require_seller),
    db: psycopg.Connection = Depends(get_db),
):
    if seller["id"] != seller_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Bạn không có quyền xác nhận giao dịch của người bán khác.")
    payment = _get_payment(db, order_id, seller_id)
    if payment["status"] != "pending":
        raise HTTPException(status.HTTP_409_CONFLICT, f"Giao dịch này đang ở trạng thái '{payment['status']}'.")
    db.execute("UPDATE order_payments SET seller_confirmed_at = CURRENT_TIMESTAMP WHERE id = %s", (payment["id"],))
    payment = _get_payment(db, order_id, seller_id)
    _try_complete_payment(db, payment)
    _recompute_order_status(db, order_id)
    order = db.execute("SELECT * FROM orders WHERE id = %s", (order_id,)).fetchone()
    if payment["status"] != "completed":
        notify(db, order["buyer_id"], "seller_received", "Người bán báo đã nhận tiền",
               f"Người bán đã xác nhận nhận được tiền cho đơn #{order_id} — vui lòng xác nhận bạn đã chuyển khoản nếu chưa.",
               order_id=order_id)
    return _row_to_order(db, order)


@router.post("/{order_id}/payments/{seller_id}/fail", response_model=OrderOut)
def fail_payment(
    order_id: int, seller_id: int,
    user: dict = Depends(get_current_user),
    db: psycopg.Connection = Depends(get_db),
):
    order = db.execute("SELECT * FROM orders WHERE id = %s", (order_id,)).fetchone()
    if order is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy đơn hàng.")
    if order["buyer_id"] != user["id"] and seller_id != user["id"]:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Bạn không liên quan đến giao dịch này.")
    payment = _get_payment(db, order_id, seller_id)
    if payment["status"] != "pending":
        raise HTTPException(status.HTTP_409_CONFLICT, f"Giao dịch này đang ở trạng thái '{payment['status']}'.")
    db.execute("UPDATE order_payments SET status = 'failed' WHERE id = %s", (payment["id"],))
    _recompute_order_status(db, order_id)
    other_party = seller_id if user["id"] == order["buyer_id"] else order["buyer_id"]
    notify(db, other_party, "payment_failed", "Giao dịch thất bại",
           f"Giao dịch thanh toán cho đơn #{order_id} đã được báo thất bại và đơn hàng bị huỷ.", order_id=order_id)
    order = db.execute("SELECT * FROM orders WHERE id = %s", (order_id,)).fetchone()
    return _row_to_order(db, order)


@router.patch("/{order_id}/items/{item_id}/status", response_model=OrderOut)
def update_item_status(
    order_id: int, item_id: int,
    payload: ItemStatusIn,
    seller: dict = Depends(require_seller),
    db: psycopg.Connection = Depends(get_db),
):
    if payload.item_status not in ITEM_STAGES:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"item_status phải là một trong {ITEM_STAGES}.")
    item = db.execute("SELECT * FROM order_items WHERE id = %s AND order_id = %s", (item_id, order_id)).fetchone()
    if item is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy sản phẩm trong đơn hàng này.")
    if item["seller_id"] != seller["id"]:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Bạn chỉ có thể cập nhật trạng thái sản phẩm của chính mình.")

    order = db.execute("SELECT * FROM orders WHERE id = %s", (order_id,)).fetchone()
    if order["status"] in ("pending", "cancelled"):
        raise HTTPException(status.HTTP_409_CONFLICT, "Đơn hàng chưa thanh toán xong hoặc đã huỷ, chưa thể cập nhật vận chuyển.")

    if ITEM_STAGES.index(payload.item_status) < ITEM_STAGES.index(item["item_status"]):
        raise HTTPException(status.HTTP_409_CONFLICT, "Không thể chuyển trạng thái ngược lại.")

    db.execute("UPDATE order_items SET item_status = %s WHERE id = %s", (payload.item_status, item_id))
    _recompute_order_status(db, order_id)
    notify(db, order["buyer_id"], "shipping_update", "Cập nhật đơn hàng",
           f"Đơn hàng #{order_id} vừa được cập nhật trạng thái: {payload.item_status}.", order_id=order_id)
    order = db.execute("SELECT * FROM orders WHERE id = %s", (order_id,)).fetchone()
    return _row_to_order(db, order)


@router.get("", response_model=list[OrderOut])
def my_orders(user: dict = Depends(get_current_user), db: psycopg.Connection = Depends(get_db)):
    rows = db.execute("SELECT * FROM orders WHERE buyer_id = %s ORDER BY created_at DESC", (user["id"],)).fetchall()
    return [_row_to_order(db, r) for r in rows]


@router.get("/{order_id}", response_model=OrderOut)
def get_order(order_id: int, user: dict = Depends(get_current_user), db: psycopg.Connection = Depends(get_db)):
    order = _owned_order(db, order_id, user["id"])
    return _row_to_order(db, order)
