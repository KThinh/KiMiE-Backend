"""Tạo thông báo trong app (bảng notifications) — dùng chung cho các router
cần báo cho buyer/seller biết có sự kiện mới (đơn hàng mới, xác nhận thanh toán,
cập nhật vận chuyển...). Không gửi email/SMS thật, chỉ lưu vào DB để hiển thị
trong mục "Thông báo" của tài khoản."""

import psycopg


def notify(db: psycopg.Connection, user_id: int, type_: str, title: str, message: str, order_id: int | None = None) -> None:
    db.execute(
        "INSERT INTO notifications (user_id, type, title, message, order_id) VALUES (%s, %s, %s, %s, %s)",
        (user_id, type_, title, message, order_id),
    )
