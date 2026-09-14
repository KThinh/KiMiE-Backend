import sqlite3

from fastapi import APIRouter, Depends, HTTPException, status

from app.database import get_db
from app.deps import get_current_user
from app.schemas import OrderCreateIn, OrderItemOut, OrderOut

router = APIRouter(prefix="/api/orders", tags=["orders"])

# khớp đúng VOUCHERS trong script.js (frontend) — 1 mã / hoá đơn
VOUCHERS = {
    "GIULUA10": {"type": "pct", "val": 10},
    "TINHHOA15": {"type": "pct", "val": 15},
    "FREESHIP": {"type": "amt", "val": 30_000},
}


def _discount_of(code: str | None, subtotal: float) -> float:
    if not code:
        return 0
    v = VOUCHERS.get(code)
    if v is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Mã voucher '{code}' không hợp lệ.")
    if v["type"] == "pct":
        return min(subtotal, round(subtotal * v["val"] / 100))
    return min(subtotal, v["val"])


def _row_to_order(db: sqlite3.Connection, order: sqlite3.Row) -> OrderOut:
    items = db.execute(
        """SELECT oi.product_id, p.name AS product_name, oi.seller_id, oi.quantity, oi.price_at_purchase
           FROM order_items oi JOIN products p ON p.id = oi.product_id
           WHERE oi.order_id = ?""",
        (order["id"],),
    ).fetchall()
    return OrderOut(
        id=order["id"],
        status=order["status"],
        voucher_code=order["voucher_code"],
        discount_amount=order["discount_amount"],
        total_price=order["total_price"],
        recipient_name=order["recipient_name"],
        recipient_email=order["recipient_email"],
        recipient_phone=order["recipient_phone"],
        shipping_address=order["shipping_address"],
        created_at=order["created_at"],
        items=[OrderItemOut(**dict(i)) for i in items],
    )


@router.post("", response_model=OrderOut, status_code=status.HTTP_201_CREATED)
def create_order(
    payload: OrderCreateIn,
    user: sqlite3.Row = Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db),
):
    subtotal = 0.0
    resolved = []  # (product_row, quantity)
    for item in payload.items:
        product = db.execute("SELECT * FROM products WHERE id = ?", (item.product_id,)).fetchone()
        if product is None or product["status"] != "active":
            raise HTTPException(status.HTTP_404_NOT_FOUND, f"Sản phẩm #{item.product_id} không còn bán.")
        if product["stock"] < item.quantity:
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                f"'{product['name']}' chỉ còn {product['stock']} sản phẩm, không đủ số lượng bạn đặt.",
            )
        subtotal += product["price"] * item.quantity
        resolved.append((product, item.quantity))

    discount = _discount_of(payload.voucher_code, subtotal)
    total = subtotal - discount

    cur = db.execute(
        """INSERT INTO orders
               (buyer_id, recipient_name, recipient_email, recipient_phone, shipping_address,
                voucher_code, discount_amount, total_price, status)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending')""",
        (
            user["id"], payload.recipient_name, payload.recipient_email, payload.recipient_phone,
            payload.shipping_address, payload.voucher_code, discount, total,
        ),
    )
    order_id = cur.lastrowid
    for product, qty in resolved:
        db.execute(
            "INSERT INTO order_items (order_id, product_id, seller_id, quantity, price_at_purchase) VALUES (?, ?, ?, ?, ?)",
            (order_id, product["id"], product["seller_id"], qty, product["price"]),
        )

    order = db.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
    return _row_to_order(db, order)


def _owned_order(db: sqlite3.Connection, order_id: int, buyer_id: int) -> sqlite3.Row:
    order = db.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
    if order is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy đơn hàng.")
    if order["buyer_id"] != buyer_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Đây không phải đơn hàng của bạn.")
    return order


@router.post("/{order_id}/confirm-payment", response_model=OrderOut)
def confirm_payment(
    order_id: int,
    user: sqlite3.Row = Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db),
):
    order = _owned_order(db, order_id, user["id"])
    if order["status"] != "pending":
        raise HTTPException(status.HTTP_409_CONFLICT, f"Đơn hàng đang ở trạng thái '{order['status']}', không thể xác nhận thanh toán.")

    # chặn oversell tối thiểu: re-check tồn kho ngay trước khi chốt đơn (giỏ hàng có thể đã
    # nằm chờ một lúc); trigger trg_order_completed_update_stock sẽ trừ kho thật sau UPDATE dưới đây
    items = db.execute(
        """SELECT oi.product_id, oi.quantity, p.name, p.stock
           FROM order_items oi JOIN products p ON p.id = oi.product_id
           WHERE oi.order_id = ?""",
        (order_id,),
    ).fetchall()
    for it in items:
        if it["stock"] < it["quantity"]:
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                f"'{it['name']}' vừa hết hàng trong lúc chờ thanh toán — vui lòng liên hệ hỗ trợ.",
            )

    db.execute("UPDATE orders SET status = 'completed' WHERE id = ?", (order_id,))
    order = db.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
    return _row_to_order(db, order)


@router.get("", response_model=list[OrderOut])
def my_orders(user: sqlite3.Row = Depends(get_current_user), db: sqlite3.Connection = Depends(get_db)):
    rows = db.execute("SELECT * FROM orders WHERE buyer_id = ? ORDER BY created_at DESC", (user["id"],)).fetchall()
    return [_row_to_order(db, r) for r in rows]


@router.get("/{order_id}", response_model=OrderOut)
def get_order(order_id: int, user: sqlite3.Row = Depends(get_current_user), db: sqlite3.Connection = Depends(get_db)):
    order = _owned_order(db, order_id, user["id"])
    return _row_to_order(db, order)
