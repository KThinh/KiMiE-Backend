---
title: KIMVIE Backend
emoji: 🛍️
colorFrom: yellow
colorTo: orange
sdk: gradio
app_file: app.py
pinned: false
---

# KIMVIE Backend

Backend **FastAPI + SQLite** cho website KIMVIE ([`KiMViE-Website`](../KiMViE-Website)) — thay toàn bộ phần
"giả lập" bằng `localStorage` trước đây bằng dữ liệu thật: đăng ký/đăng nhập có mật khẩu thật (băm PBKDF2,
không bao giờ lưu chuỗi gốc), sản phẩm người bán đăng lên được **mọi người ghé site đều thấy** (không chỉ
riêng máy người đăng) và **sửa lại được bất cứ lúc nào** (tồn kho, mô tả, ảnh, giá, ẩn/hiện...), đặt hàng
tạo ra đơn hàng thật trong database, tồn kho/số lượng đã bán tự cập nhật qua trigger SQL khi đơn hàng hoàn
tất, và người mua đánh giá 1-5 sao kèm bình luận cho từng sản phẩm — điểm trung bình cũng do trigger tự tính.

## Chạy thử (2 lệnh)

```bash
pip install -r requirements.txt
python create_db.py        # tạo database.db kèm dữ liệu mẫu (chỉ cần chạy 1 lần, hoặc lại từ đầu bất cứ lúc nào)
uvicorn app.app:app --reload
```

Mở **http://127.0.0.1:8000** — server này phục vụ luôn cả trang web tĩnh (mount thư mục `../KiMViE-Website`,
xem `KV_FRONTEND_DIR` trong `.env.example`) lẫn API, nên không cần chạy 2 server riêng và không bị CORS.
Muốn đổi cấu hình (khoá JWT, đường dẫn frontend...) thì copy `.env.example` → `.env` rồi sửa.

File [`app.py`](app.py) ở gốc repo là entry point riêng cho Hugging Face Spaces (SDK Gradio, xem phần
Deploy bên dưới) — không cần dùng khi chạy local, `uvicorn app.app:app --reload` vẫn là cách chạy chính.

Tài liệu API tự sinh (Swagger UI): **http://127.0.0.1:8000/docs**

### Tài khoản mẫu (mật khẩu đều là `demo123`)

| Email | Vai trò |
|---|---|
| `tranvanminh.battrang@kimvie.vn` | Người bán — Gốm Minh Long Bát Tràng |
| `nguyenthihoa.vanphuc@kimvie.vn` | Người bán — Lụa Hoa Vạn Phúc |
| `levanphu.phuvinh@kimvie.vn` | Người bán — Mây Tre Phú An |
| `phamthilan@gmail.com` | Người mua |
| `dominhkhang@gmail.com` | Người mua |

## Cấu trúc

```
app.py            Entry point Hugging Face Spaces (SDK Gradio) — xem phần Deploy bên dưới
app/
  app.py          FastAPI app: CORS, mount frontend tĩnh, include các router
  config.py       đọc biến môi trường (.env), đường dẫn DB/frontend, khoá JWT
  security.py     băm mật khẩu (PBKDF2-HMAC-SHA256) + tạo/giải mã JWT
  database.py     kết nối SQLite dùng chung (sqlite3 thuần, không ORM)
  deps.py         dependency: get_current_user, require_seller
  schemas.py      Pydantic models (request/response)
  serializers.py  sqlite3.Row -> Pydantic (product, user)
  routers/
    auth.py       POST /api/auth/register, /login · GET /api/auth/me
    villages.py   GET /api/villages
    products.py   GET /api/products (public) · POST/PUT/DELETE (seller, chỉ sản phẩm của mình)
    seller.py     POST /api/seller/register · GET /api/seller/products, /stats
    cart.py       GET/POST/PUT/DELETE /api/cart (giỏ hàng theo tài khoản — xem ghi chú bên dưới)
    orders.py     POST /api/orders · POST /api/orders/{id}/confirm-payment · GET /api/orders
    reviews.py    GET/POST /api/products/{id}/reviews · DELETE /api/products/{id}/reviews/me
create_db.py      tạo + seed database.db (13 sản phẩm thật lấy từ script.js, 3 làng nghề, 5 user mẫu)
database-schema.md  mô tả đầy đủ schema, trigger, lý do thiết kế
```

## Vì sao là sqlite3 thuần, không dùng SQLAlchemy?

`database.db` được tạo bởi `create_db.py` với 1 **trigger SQL** (`trg_order_completed_update_stock`) tự
cộng `sold_count` / trừ `stock` của sản phẩm ngay khi đơn hàng chuyển sang `completed` — logic nghiệp vụ
này nằm ở tầng database, không phải Python. Dùng ORM sẽ phải định nghĩa lại schema ở 2 nơi (Python model +
file .sql) mà vẫn không tận dụng được trigger. Giữ sqlite3 thuần + SQL viết tay giúp 1 nguồn schema duy nhất
(`create_db.py`) và trigger hoạt động đúng như thiết kế.

## Điểm đã cố ý đơn giản hoá (ghi rõ để không hiểu nhầm là bug)

- **Giỏ hàng vẫn ưu tiên `localStorage` phía frontend** cho khách chưa đăng nhập (giữ đúng trải nghiệm gốc:
  thêm vào giỏ không cần đăng nhập). API `/api/cart` đã có sẵn và hoạt động đầy đủ nếu sau này muốn nâng
  cấp lên giỏ hàng đồng bộ theo tài khoản — chỉ cần nối vào frontend.
- **Đăng nhập bắt buộc mới thanh toán được** (đặt hàng cần biết `buyer_id` thật) — khi bấm "Tiến hành thanh
  toán" mà chưa đăng nhập, trang tự mở form đăng nhập.
- **Không khoá tồn kho khi tạo đơn `pending`** — `POST /api/orders` kiểm tra tồn kho tại thời điểm tạo đơn,
  nhưng không "giữ chỗ". `confirm-payment` kiểm tra lại lần nữa trước khi chốt, nhưng 2 đơn `pending` cùng
  lúc lý thuyết vẫn có thể cùng vượt qua kiểm tra đầu — chấp nhận được cho quy mô demo, cần khoá dòng
  (`SELECT ... FOR UPDATE`-style) nếu triển khai thật với lượng truy cập cao.
- **Voucher không giới hạn số lần dùng** — 3 mã cố định (`GIULUA10`, `TINHHOA15`, `FREESHIP`) trong
  `app/routers/orders.py`, khớp với bảng tương ứng ở frontend, ai cũng dùng lại được nhiều lần.
- **`KV_JWT_SECRET` mặc định chỉ để demo** — bắt buộc đặt biến môi trường riêng trước khi deploy thật
  (xem cảnh báo lúc khởi động server).

## Đổi mật khẩu thật khi deploy

`create_db.py`/`app/security.py` băm mật khẩu bằng PBKDF2-HMAC-SHA256 (200,000 vòng lặp, salt riêng từng
user) — an toàn hơn hẳn SHA-256 trần của bản demo cũ, nhưng khi triển khai thật nên cân nhắc `bcrypt`/`argon2`
(qua thư viện `passlib`) để chuẩn hoá theo khuyến nghị OWASP hiện hành.

## Deploy lên Hugging Face Spaces (SDK Gradio)

Space này chọn SDK **Gradio** (không phải Docker) — HF chỉ chạy thẳng `python app.py`, không có
shell để gõ lệnh nên toàn bộ phần build/khởi tạo phải tự động hoá trong code:

1. Tạo Space mới trên [huggingface.co/new-space](https://huggingface.co/new-space), chọn SDK **Gradio**.
2. Push toàn bộ repo này lên Space (`git remote add space https://huggingface.co/spaces/<user>/<space-name>`
   rồi `git push space main`). Khối YAML ở đầu file README.md này (`sdk: gradio`, `app_file: app.py`) là
   phần cấu hình Space bắt buộc — đừng xoá.
3. `requirements.txt` đã có sẵn `gradio` — Space tự cài, không cần làm gì thêm.
4. Vào **Settings → Variables and secrets** của Space, đặt ít nhất `KV_JWT_SECRET` (bắt buộc, xem cảnh báo
   lúc khởi động server nếu quên) và tuỳ chọn `KV_TOKEN_EXPIRE_MINUTES`. **Không đặt `KV_DB_PATH`/
   `KV_FRONTEND_DIR`** trừ khi biết rõ cần đổi — giá trị mặc định (`database.db` cạnh `create_db.py`,
   không mount frontend nếu không thấy repo `KiMViE-Website` cạnh bên) đã đúng cho kiểu deploy backend-only.
5. Khi Space khởi động, [`app.py`](app.py) mount app FastAPI thật (từ [`app/app.py`](app/app.py)) cùng 1
   giao diện Gradio nhỏ tại `/gradio` (cho đúng quy ước SDK), rồi tự chạy uvicorn ở cổng `7860` — cổng cố
   định Spaces dùng cho mọi SDK không phải Docker. `check_database()` trong `app/app.py` tự chạy
   `create_db.py` để tạo + seed `database.db` nếu chưa có, vì Space không có cách nào để chạy lệnh đó
   thủ công.
6. **Lưu ý filesystem của Space là ephemeral** — mỗi lần Space restart/rebuild (kể cả khi chỉ sleep rồi
   thức dậy sau thời gian rảnh trên gói free) thì `database.db` bị tạo lại từ đầu với dữ liệu mẫu, **mất
   hết đơn hàng/sản phẩm/đánh giá thật** đã phát sinh trong lúc chạy. Muốn dữ liệu tồn tại lâu dài thì bật
   **Persistent Storage** (tính phí) trong Settings của Space, mount vào `/data`, rồi đặt
   `KV_DB_PATH=/data/database.db`.
7. Trang web tĩnh (`KiMViE-Website`) sẽ **không** được mount trừ khi repo đó cũng nằm trong chính Space
   này (Spaces chỉ có 1 repo duy nhất, không tự thấy được repo `KiMViE-Website` nằm ngoài như lúc chạy
   local) — nếu muốn phục vụ luôn cả frontend từ Space, copy nội dung `KiMViE-Website` vào 1 thư mục con
   của repo backend rồi trỏ `KV_FRONTEND_DIR` tới đó; nếu không thì Space này chỉ đóng vai trò API, còn
   frontend deploy/host ở chỗ khác và gọi API qua URL của Space (CORS đã mở `allow_origins=["*"]`).
