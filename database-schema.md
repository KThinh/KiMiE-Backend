# Mô tả Database — Website KIMVIE (môn Trải nghiệm khởi nghiệp)

Database dùng **SQLite** — toàn bộ lưu trong 1 file `database.db` duy nhất, không cần cài đặt server riêng.

> Bản này thay cho bản mô tả cũ (role `buyer`/`seller` loại trừ nhau). Bản mới khớp với giao diện web
> thật đang chạy: **mọi tài khoản mặc định là buyer**, và có thể **đăng ký thêm vai trò seller**
> (không mất khả năng mua hàng) — đúng với luồng "Đăng ký làm người bán" trong trang tài khoản.
> Đồng thời bổ sung các cột còn thiếu để quản lý một gian hàng thật: **tồn kho, số lượng đã bán,
> điểm đánh giá, trạng thái đăng bán**, và bảng **làng nghề** để lọc/tra cứu thay vì chuỗi tự do.

---

## 1. Bảng `villages` — làng nghề (mới)

Tra cứu 3 làng nghề cốt lõi của KIMVIE, dùng làm khoá ngoại cho `products` và `seller_profiles`
thay vì lặp lại chuỗi `'bt' / 'vp' / 'pv'` rải rác — tránh gõ sai, dễ thêm làng nghề mới sau này.

| Cột | Kiểu | Mô tả |
|---|---|---|
| `id` | INTEGER, PK, AUTOINCREMENT | Mã làng nghề |
| `code` | TEXT, UNIQUE | `'bt'` / `'vp'` / `'pv'` — khớp `data-v` trên web |
| `name` | TEXT | Tên hiển thị: Bát Tràng / Vạn Phúc / Phú Vinh |
| `craft` | TEXT | Nghề: Gốm sứ / Lụa tơ tằm / Mây tre đan |
| `description` | TEXT | Mô tả ngắn (lấy từ trang chủ) |

## 2. Bảng `users`

Tài khoản dùng chung cho buyer & seller.

| Cột | Kiểu | Mô tả |
|---|---|---|
| `id` | INTEGER, PK, AUTOINCREMENT | Mã định danh người dùng |
| `name` | TEXT | Tên hiển thị |
| `email` | TEXT, UNIQUE | Email đăng nhập |
| `phone` | TEXT | Số điện thoại |
| `password_hash` | TEXT | Mật khẩu đã mã hoá (không lưu mật khẩu gốc) |
| `is_seller` | INTEGER (0/1) | **Mới** — 1 nếu đã đăng ký kênh người bán. Thay cho cột `role` cũ vì 1 user vừa mua vừa bán được, không loại trừ nhau |
| `created_at` | DATETIME | Thời điểm tạo tài khoản |

## 3. Bảng `seller_profiles` — hồ sơ gian hàng (mới, tách khỏi `users`)

Chỉ tồn tại với user có `is_seller = 1`. Tách bảng riêng (quan hệ 1-1 với `users`) thay vì nhét
thẳng các cột gian hàng vào `users`, để buyer thường không có một đống cột rỗng vô nghĩa.
Khớp đúng 4 trường trên form "Đăng ký làm người bán" của web: tên gian hàng, làng nghề, SĐT, giới thiệu.

| Cột | Kiểu | Mô tả |
|---|---|---|
| `id` | INTEGER, PK, AUTOINCREMENT | Mã hồ sơ |
| `user_id` | INTEGER, UNIQUE, FK → `users.id` | Chủ gian hàng |
| `shop_name` | TEXT | Tên gian hàng / nghệ nhân |
| `village_id` | INTEGER, FK → `villages.id` | Gian hàng thuộc làng nghề nào |
| `phone` | TEXT | SĐT liên hệ gian hàng (có thể khác `users.phone`) |
| `bio` | TEXT | Giới thiệu ngắn |
| `created_at` | DATETIME | Thời điểm đăng ký làm người bán |

## 4. Bảng `products`

Sản phẩm do seller đăng. So với bản cũ, bổ sung `village_id`, `sold_count`, `rating`, `status`, `updated_at`.

| Cột | Kiểu | Mô tả |
|---|---|---|
| `id` | INTEGER, PK, AUTOINCREMENT | Mã sản phẩm |
| `seller_id` | INTEGER, FK → `users.id` | Sản phẩm thuộc seller nào |
| `village_id` | INTEGER, FK → `villages.id` | **Mới** — dùng để lọc theo làng nghề trên Sàn thương mại |
| `name` | TEXT | Tên sản phẩm |
| `description` | TEXT | Mô tả sản phẩm |
| `price` | REAL | Giá bán (> 0) |
| `stock` | INTEGER | **Tồn kho** — số lượng còn lại có thể bán |
| `sold_count` | INTEGER | **Mới — đã bán**. Tự động cộng dồn khi 1 đơn hàng chứa sản phẩm này chuyển sang `completed` (xem trigger bên dưới); không tự sửa tay ở tầng ứng dụng để tránh lệch với đơn hàng thật |
| `rating` | REAL | **Mới** — điểm đánh giá trung bình (0–5), mặc định 5.0, khớp huy hiệu "★ 4.9" trên thẻ sản phẩm |
| `image_url` | TEXT | Đường dẫn ảnh sản phẩm |
| `status` | TEXT | **Mới** — `'active'` (đang bán) / `'hidden'` (seller tạm ẩn khỏi Sàn thương mại) |
| `created_at` | DATETIME | Thời điểm đăng sản phẩm |
| `updated_at` | DATETIME | **Mới** — thời điểm sửa gần nhất |

## 5. Bảng `cart_items`

Giỏ hàng tạm thời của buyer, xoá các dòng liên quan sau khi checkout thành công.

| Cột | Kiểu | Mô tả |
|---|---|---|
| `id` | INTEGER, PK, AUTOINCREMENT | Mã dòng giỏ hàng |
| `buyer_id` | INTEGER, FK → `users.id` | Giỏ hàng của buyer nào |
| `product_id` | INTEGER, FK → `products.id` | Sản phẩm được thêm vào giỏ |
| `quantity` | INTEGER | Số lượng (> 0) |
| `added_at` | DATETIME | **Mới** — thời điểm thêm vào giỏ |

Ràng buộc `UNIQUE(buyer_id, product_id)`: mỗi buyer chỉ có 1 dòng cho 1 sản phẩm — thêm lần 2 thì
cộng dồn `quantity` ở tầng ứng dụng (`UPDATE ... SET quantity = quantity + ?`) thay vì tạo dòng mới,
khớp đúng hành vi nút "+"/"–" trong giỏ hàng trên web.

## 6. Bảng `orders`

Đơn hàng sau khi buyer checkout. Bổ sung các trường khớp với 3 bước checkout trên web
(thông tin nhận hàng ở bước 2, mã voucher ở bước 1) thay vì chỉ có `total_price` trơn.

| Cột | Kiểu | Mô tả |
|---|---|---|
| `id` | INTEGER, PK, AUTOINCREMENT | Mã đơn hàng |
| `buyer_id` | INTEGER, FK → `users.id` | Người đặt đơn |
| `recipient_name` | TEXT | **Mới** — tên người nhận (form checkout bước 2) |
| `recipient_email` | TEXT | **Mới** — email nhận xác nhận đơn |
| `recipient_phone` | TEXT | **Mới** — SĐT người nhận |
| `shipping_address` | TEXT | **Mới** — địa chỉ giao hàng |
| `voucher_code` | TEXT | **Mới** — mã giảm giá đã áp (VD `GIULUA10`), NULL nếu không dùng |
| `discount_amount` | REAL | **Mới** — số tiền đã giảm |
| `total_price` | REAL | Tổng giá trị đơn hàng (sau giảm giá) |
| `status` | TEXT | `'pending'` / `'completed'` / `'cancelled'` |
| `created_at` | DATETIME | Thời điểm đặt hàng |

## 7. Bảng `order_items`

Chi tiết từng sản phẩm trong 1 đơn hàng (1 đơn có thể chứa nhiều sản phẩm, từ nhiều seller khác nhau).

| Cột | Kiểu | Mô tả |
|---|---|---|
| `id` | INTEGER, PK, AUTOINCREMENT | Mã dòng chi tiết đơn |
| `order_id` | INTEGER, FK → `orders.id` | Thuộc đơn hàng nào |
| `product_id` | INTEGER, FK → `products.id` | Sản phẩm được mua |
| `seller_id` | INTEGER, FK → `users.id` | Lưu sẵn seller để seller dễ truy vấn đơn hàng liên quan đến mình |
| `quantity` | INTEGER | Số lượng mua (> 0) |
| `price_at_purchase` | REAL | Giá tại thời điểm mua (không đổi dù sau này seller sửa giá gốc) |

---

## Sơ đồ quan hệ

```
villages (1) ───< products (village_id)
villages (1) ───< seller_profiles (village_id)
users (1) ───< seller_profiles (user_id, 1-1)
users (1) ───< products (seller_id)
users (1) ───< cart_items (buyer_id)
users (1) ───< orders (buyer_id)
users (1) ───< order_items (seller_id)
products (1) ───< cart_items (product_id)
products (1) ───< order_items (product_id)
orders (1) ───< order_items (order_id)
```

---

## Trigger tự động: cập nhật tồn kho / đã bán

Đây là phần khác biệt lớn nhất so với bản cũ — thay vì để tầng ứng dụng tự tay `UPDATE` cả
`stock` lẫn `sold_count` mỗi nơi xử lý thanh toán (dễ quên/lệch dữ liệu), database tự làm việc
đó ngay khi đơn hàng chuyển trạng thái sang `completed`:

```sql
CREATE TRIGGER trg_order_completed_update_stock
AFTER UPDATE OF status ON orders
WHEN NEW.status = 'completed' AND OLD.status <> 'completed'
BEGIN
    UPDATE products
    SET sold_count = sold_count + (
            SELECT quantity FROM order_items
            WHERE order_items.order_id = NEW.id AND order_items.product_id = products.id
        ),
        stock = MAX(0, stock - (
            SELECT quantity FROM order_items
            WHERE order_items.order_id = NEW.id AND order_items.product_id = products.id
        ))
    WHERE id IN (SELECT product_id FROM order_items WHERE order_id = NEW.id);
END;
```

**Giới hạn đã biết (chưa xử lý, ghi chú để làm sau nếu cần):** nếu một đơn `completed` bị chuyển
tiếp sang `cancelled`, trigger hiện tại **không** hoàn lại `stock`/`sold_count` — cần thêm 1 trigger
đối xứng nếu nghiệp vụ thực tế cho phép huỷ đơn sau khi đã xác nhận thanh toán.

---

## Câu lệnh tạo bảng đầy đủ + index

Xem file [`create_db.py`](create_db.py) — chạy `python create_db.py` sẽ tạo lại `database.db` từ đầu
**kèm dữ liệu mẫu thật** (3 làng nghề, 3 seller + 2 buyer, đúng 13 sản phẩm đang hiển thị trên Sàn
thương mại lấy từ `script.js`, 1 giỏ hàng mẫu, 1 đơn hàng mẫu đã `completed` để minh hoạ trigger
hoạt động). File tạo ra dùng được ngay để demo/truy vấn thử, không phải các bảng rỗng.

Các index đã tạo sẵn (khoá ngoại hay dùng để lọc/JOIN):

```sql
CREATE INDEX idx_products_seller     ON products(seller_id);
CREATE INDEX idx_products_village    ON products(village_id);
CREATE INDEX idx_seller_profiles_v   ON seller_profiles(village_id);
CREATE INDEX idx_cart_buyer          ON cart_items(buyer_id);
CREATE INDEX idx_orders_buyer        ON orders(buyer_id);
CREATE INDEX idx_order_items_order   ON order_items(order_id);
CREATE INDEX idx_order_items_seller  ON order_items(seller_id);
```

---

## Ghi chú thiết kế

- **Phân quyền buyer/seller**: xử lý ở tầng backend (API), dựa vào cột `is_seller` trong session
  đăng nhập — không phải ở database. Ví dụ: API tạo sản phẩm sẽ kiểm tra
  `req.session.user.is_seller === 1` trước khi cho phép ghi vào bảng `products`.
- **Không lưu mật khẩu gốc**: `password_hash` phải được mã hoá bằng thư viện như `bcrypt`/`argon2`
  trước khi lưu. File `create_db.py` chỉ băm SHA-256 cho dữ liệu demo — **không dùng cách này cho
  backend thật**, SHA-256 trần không có salt, dễ bị dò ngược bằng bảng cầu vồng.
- **`price_at_purchase`**: tách riêng khỏi `products.price` để lịch sử đơn hàng không bị thay đổi
  nếu seller sửa giá sản phẩm sau này.
- **`sold_count` không tự suy ra bằng `SUM(order_items.quantity)` mỗi lần đọc**: cố tình lưu thành
  cột riêng (denormalize) để trang Sàn thương mại đọc nhanh mà không phải JOIN/SUM qua 3 bảng mỗi
  lần hiển thị danh sách sản phẩm — đổi lại phải giữ đúng bằng trigger ở trên.
