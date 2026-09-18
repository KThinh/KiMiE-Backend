# Mô tả Database — Website KIMVIE (môn Trải nghiệm khởi nghiệp)

Database dùng **PostgreSQL** (Render). Nguồn sự thật duy nhất cho schema là
[`create_db.py`](create_db.py) — script này DROP + CREATE + seed lại toàn bộ mỗi lần chạy
(`python create_db.py`), không có hệ thống migration riêng.

> Bản này thay cho bản mô tả cũ. Thay đổi lớn nhất: **đăng nhập bằng username** (không còn
> bằng email), và bổ sung cả một tầng thương mại điện tử đầy đủ: nhiều ảnh/sản phẩm, màu/size,
> wishlist, sổ địa chỉ, thanh toán theo từng seller (QR riêng + xác nhận 2 chiều), trạng thái
> vận chuyển theo từng dòng hàng, và thông báo trong app.

---

## 1. Bảng `villages` — làng nghề

| Cột | Kiểu | Mô tả |
|---|---|---|
| `id` | SERIAL PK | Mã làng nghề |
| `code` | TEXT UNIQUE | `'bt'` / `'vp'` / `'pv'` |
| `name` | TEXT | Tên hiển thị |
| `craft` | TEXT | Nghề |
| `description` | TEXT | Mô tả ngắn |

## 2. Bảng `users`

| Cột | Kiểu | Mô tả |
|---|---|---|
| `id` | SERIAL PK | |
| `name` | TEXT | Tên hiển thị |
| `username` | TEXT UNIQUE | **Đăng nhập bằng cột này** (không còn dùng email) |
| `email` | TEXT UNIQUE | Chỉ còn là thông tin liên hệ/nhận thông báo |
| `phone` | TEXT | |
| `avatar_url` | TEXT | Ảnh đại diện (data URI, giống cách lưu ảnh sản phẩm) |
| `password_hash` | TEXT | PBKDF2-HMAC-SHA256 (xem `app/security.py`) |
| `is_seller` | INTEGER (0/1) | 1 nếu đã đăng ký kênh người bán |
| `created_at` | TIMESTAMP | |

## 3. Bảng `seller_profiles` (1-1 với `users`)

| Cột | Kiểu | Mô tả |
|---|---|---|
| `id` | SERIAL PK | |
| `user_id` | INTEGER UNIQUE FK → `users.id` | |
| `shop_name` | TEXT | |
| `village_id` | INTEGER FK → `villages.id` | |
| `phone` | TEXT | |
| `bio` | TEXT | |
| `payment_qr_url` | TEXT | **Mới** — ảnh mã QR nhận tiền của gian hàng; buyer chuyển khoản thẳng vào đây khi checkout |
| `created_at` | TIMESTAMP | |

## 4. Bảng `products`

| Cột | Kiểu | Mô tả |
|---|---|---|
| `id` | SERIAL PK | |
| `seller_id` | FK → `users.id` | |
| `village_id` | FK → `villages.id` | |
| `name`, `description` | TEXT | |
| `material` | TEXT | **Mới** — chất liệu |
| `size_guide` | TEXT | **Mới** — hướng dẫn chọn size |
| `colors`, `sizes` | TEXT | **Mới** — danh sách phân cách bởi dấu phẩy, vd `"Đỏ,Xanh,Đen"` |
| `price` | DOUBLE PRECISION | Giá bán hiện tại |
| `original_price` | DOUBLE PRECISION NULL | **Mới** — có giá trị và lớn hơn `price` ⇒ sản phẩm đang sale (suy ra, không có cột `is_sale` riêng) |
| `stock`, `sold_count` | INTEGER | Tồn kho / đã bán |
| `rating`, `review_count` | | Tự tính bằng trigger từ `reviews` |
| `image_url` | TEXT | Ảnh bìa |
| `status` | TEXT | `'active'` / `'hidden'` |
| `created_at`, `updated_at` | | "Mới" (badge new) = `created_at` trong 14 ngày gần nhất, suy ra khi đọc, không lưu cột riêng |

## 5. Bảng `product_images` (mới) — bộ sưu tập ảnh ngoài ảnh bìa

`id, product_id FK, image_url, sort_order, created_at`.

## 6. Bảng `cart_items`

Thêm `color TEXT`, `size TEXT` — 1 sản phẩm với 2 màu/size khác nhau là 2 dòng giỏ hàng khác
nhau: `UNIQUE(buyer_id, product_id, color, size)`.

## 7. Bảng `wishlist_items` (mới)

`id, buyer_id FK, product_id FK, added_at`, `UNIQUE(buyer_id, product_id)`.

## 8. Bảng `addresses` (mới) — sổ địa chỉ giao hàng

`id, user_id FK, label, recipient_name, phone, address_line, is_default, created_at`.

## 9. Bảng `orders`

Thêm `shipping_method` (`'standard'`/`'express'`, phí tương ứng trong `SHIPPING_FEES` ở
`app/routers/orders.py`) và `shipping_fee`. `status` mở rộng thành
`'pending' | 'processing' | 'shipped' | 'delivered' | 'cancelled'` — **cột này được SUY RA**, ứng
dụng không cho sửa tay trực tiếp (xem `_recompute_order_status()` bên dưới).

## 10. Bảng `order_items`

Thêm `color`, `size` (chụp lại lựa chọn lúc đặt hàng) và `item_status`
(`'processing' | 'shipped' | 'delivered'`, mặc định `'processing'`) — **do chính seller sở hữu
dòng hàng đó cập nhật** khi đóng gói/giao hàng phần của mình (1 đơn có thể có nhiều seller, mỗi
seller giao hàng độc lập với tiến độ riêng).

## 11. Bảng `order_payments` (mới) — thanh toán theo từng seller

Một đơn có thể gồm sản phẩm của nhiều seller khác nhau. Mỗi seller có mặt trong đơn có đúng
**1 dòng** ở đây, chụp lại QR + số tiền phải trả cho seller đó tại thời điểm đặt hàng:

| Cột | Kiểu | Mô tả |
|---|---|---|
| `id` | SERIAL PK | |
| `order_id` | FK → `orders.id` | |
| `seller_id` | FK → `users.id` | |
| `amount` | DOUBLE PRECISION | Số tiền buyer phải chuyển cho seller này |
| `qr_image_url` | TEXT | Chụp lại `seller_profiles.payment_qr_url` lúc đặt hàng |
| `buyer_confirmed_at` | TIMESTAMP NULL | Buyer bấm "Tôi đã chuyển khoản" |
| `seller_confirmed_at` | TIMESTAMP NULL | Seller bấm "Tôi đã nhận được tiền" |
| `status` | TEXT | `'pending'` → `'completed'` (cả 2 xác nhận) hoặc `'failed'` (1 trong 2 bên báo lỗi) |

`UNIQUE(order_id, seller_id)`. Khi `status` chuyển thành `'completed'`, trigger
`trg_payment_completed_update_stock` tự trừ tồn kho + cộng `sold_count` **chỉ cho các
`order_items` của đúng seller đó trong đơn** (không đụng vào phần hàng của seller khác trong
cùng đơn) — xem hàm `fn_payment_completed_update_stock()` trong `create_db.py`. Nếu `'failed'`,
không có gì bị trừ vì chưa từng `'completed'`.

`orders.status` được ứng dụng suy ra lại (`_recompute_order_status()` trong
`app/routers/orders.py`, chạy sau mỗi lần đổi `order_payments.status` hoặc
`order_items.item_status`, không phải trigger DB):
`cancelled` nếu có bất kỳ payment nào `failed`; ngược lại `pending` nếu chưa đủ payment
`completed`; ngược lại là giai đoạn thấp nhất trong `item_status` của các `order_items`
(`processing` → `shipped` → `delivered`).

## 12. Bảng `notifications` (mới)

`id, user_id FK (người nhận), type, title, message, order_id FK NULL, is_read, created_at`.
Chỉ là thông báo trong app (mục "Thông báo" của tài khoản) — không gửi email/SMS thật. Tạo bằng
hàm `notify()` trong `app/notify.py`, gọi khi: có đơn hàng mới (báo seller), buyer/seller xác
nhận thanh toán (báo bên còn lại), giao dịch thất bại, cập nhật trạng thái vận chuyển (báo buyer).

## 13. Bảng `reviews` + `review_images` (mới)

`reviews` giữ nguyên (`UNIQUE(product_id, buyer_id)`, upsert khi đánh giá lại). Ảnh đính kèm
tách bảng riêng `review_images (id, review_id FK ON DELETE CASCADE, image_url)` vì 1 đánh giá có
thể có nhiều ảnh. **Ràng buộc mới ở tầng API** (không phải constraint DB): chỉ được đánh giá sản
phẩm mà buyer có ít nhất 1 `order_items.item_status = 'delivered'` cho sản phẩm đó — xem
`app/routers/reviews.py::upsert_review`.

---

## Sơ đồ quan hệ (rút gọn)

```
villages (1) ───< products (village_id)
villages (1) ───< seller_profiles (village_id)
users (1) ───< seller_profiles (user_id, 1-1)
users (1) ───< products (seller_id)
users (1) ───< cart_items, wishlist_items, addresses (buyer/user_id)
users (1) ───< orders (buyer_id)
users (1) ───< order_items, order_payments (seller_id)
users (1) ───< notifications (user_id)
products (1) ───< product_images, cart_items, wishlist_items, order_items, reviews
orders (1) ───< order_items, order_payments
reviews (1) ───< review_images
```

---

## Trigger tự động trong database

1. **`trg_payment_completed_update_stock`** (AFTER UPDATE OF status ON `order_payments`, khi
   chuyển sang `'completed'`) — trừ `stock` / cộng `sold_count` cho đúng các `order_items` của
   seller đó trong đơn đó. Thay thế cho trigger `trg_order_completed_update_stock` cũ (vốn gắn
   vào `orders.status`, không còn phù hợp khi 1 đơn có nhiều seller thanh toán độc lập).
2. **`trg_reviews_after_insert/update/delete`** — giữ `products.rating`/`review_count` luôn khớp
   với bảng `reviews` (không đổi so với bản trước).

Xem đầy đủ trong [`create_db.py`](create_db.py).

**Giới hạn đã biết**: nếu một `order_payments` `'completed'` cần đảo ngược (hoàn tiền/huỷ sau
khi đã giao), không có trigger đối xứng hoàn lại `stock`/`sold_count` — chưa có nghiệp vụ hoàn
tiền trong phạm vi hiện tại.

---

## Ghi chú thiết kế

- **Phân quyền buyer/seller**: xử lý ở tầng backend (`Depends(require_seller)`), dựa vào cột
  `is_seller`, không phải ở database.
- **`price_at_purchase`**: tách riêng khỏi `products.price` để lịch sử đơn hàng không đổi nếu
  seller sửa giá sau này.
- **`sold_count`/`rating`/`review_count` không tự suy ra mỗi lần đọc**: cố tình denormalize để
  trang Shop/Product đọc nhanh — đổi lại phải giữ đúng bằng trigger.
- **Thanh toán không qua cổng thật**: đây là dự án học tập, không tích hợp cổng thanh toán thật
  (Stripe/VNPay/MoMo...). Mỗi seller tự upload QR ngân hàng/ví của họ; hệ thống chỉ theo dõi
  trạng thái "đã xác nhận" 2 chiều giữa buyer/seller, không thực sự di chuyển tiền.
