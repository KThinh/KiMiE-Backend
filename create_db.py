"""
Tạo schema (bảng, index, trigger) trong PostgreSQL theo đúng cấu trúc mô tả trong
database-schema.md, đồng thời chèn sẵn dữ liệu mẫu lấy từ chính giao diện trang web
(24 sản phẩm: 13 sản phẩm gốc trong script.js + 11 món đồ dùng giá mềm, 3 làng nghề,
người bán/người mua mẫu) để database
dùng được ngay cho việc demo/truy vấn thử — không phải bảng rỗng.

Đăng nhập giờ dùng USERNAME (không còn dùng email). Mật khẩu demo của mọi user mẫu
là "demo123", băm bằng đúng hàm app.security.hash_password mà FastAPI backend dùng
để xác thực — nên có thể đăng nhập thật qua POST /api/auth/login bằng username của
họ (vd. username "minh") ngay sau khi seed xong.

Cách dùng (chạy ở thư mục gốc repo, cùng cấp với thư mục app/, đã đặt KV_DATABASE_URL
trong .env hoặc biến môi trường):
    python create_db.py

CHÚ Ý: script này XOÁ SẠCH (DROP CASCADE) toàn bộ bảng cũ rồi tạo lại từ đầu mỗi lần
chạy — mất hết dữ liệu thật đã ghi vào lúc chạy (đơn hàng, tài khoản mới đăng ký...).
Chỉ chạy khi thật sự muốn reset database về đúng trạng thái seed mẫu.
"""

import psycopg

from app.config import DATABASE_URL
from app.product_content import PRODUCT_CONTENT
from app.security import hash_password

DROP_TABLES_SQL = [
    "DROP TABLE IF EXISTS passport_stamps CASCADE;",
    "DROP TABLE IF EXISTS notifications CASCADE;",
    "DROP TABLE IF EXISTS order_payments CASCADE;",
    "DROP TABLE IF EXISTS review_images CASCADE;",
    "DROP TABLE IF EXISTS reviews CASCADE;",
    "DROP TABLE IF EXISTS order_items CASCADE;",
    "DROP TABLE IF EXISTS orders CASCADE;",
    "DROP TABLE IF EXISTS wishlist_items CASCADE;",
    "DROP TABLE IF EXISTS addresses CASCADE;",
    "DROP TABLE IF EXISTS cart_items CASCADE;",
    "DROP TABLE IF EXISTS product_images CASCADE;",
    "DROP TABLE IF EXISTS products CASCADE;",
    "DROP TABLE IF EXISTS seller_profiles CASCADE;",
    "DROP TABLE IF EXISTS users CASCADE;",
    "DROP TABLE IF EXISTS villages CASCADE;",
]

CREATE_TABLES_SQL = [
    """
    CREATE TABLE villages (
        id          SERIAL PRIMARY KEY,
        code        TEXT NOT NULL UNIQUE CHECK(code IN ('bt', 'vp', 'pv')),
        name        TEXT NOT NULL,
        craft       TEXT NOT NULL,
        description TEXT
    );
    """,
    """
    CREATE TABLE users (
        id            SERIAL PRIMARY KEY,
        name          TEXT NOT NULL,
        username      TEXT NOT NULL UNIQUE,
        email         TEXT NOT NULL UNIQUE,
        phone         TEXT,
        avatar_url    TEXT,
        password_hash TEXT NOT NULL,
        is_seller     INTEGER NOT NULL DEFAULT 0 CHECK(is_seller IN (0, 1)),
        created_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    """,
    """
    CREATE TABLE seller_profiles (
        id              SERIAL PRIMARY KEY,
        user_id         INTEGER NOT NULL UNIQUE REFERENCES users(id),
        shop_name       TEXT NOT NULL,
        village_id      INTEGER NOT NULL REFERENCES villages(id),
        phone           TEXT,
        bio             TEXT,
        payment_qr_url  TEXT,  -- ảnh mã QR nhận tiền của gian hàng, buyer chuyển khoản trực tiếp vào đây
        created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    """,
    """
    CREATE TABLE products (
        id             SERIAL PRIMARY KEY,
        seller_id      INTEGER NOT NULL REFERENCES users(id),
        village_id     INTEGER NOT NULL REFERENCES villages(id),
        name           TEXT NOT NULL,
        description    TEXT,
        story          TEXT,             -- câu chuyện sản phẩm
        material       TEXT,             -- chất liệu
        size_guide     TEXT,             -- hướng dẫn chọn size
        colors         TEXT,             -- danh sách màu, phân cách bởi dấu phẩy
        sizes          TEXT,             -- danh sách size, phân cách bởi dấu phẩy
        price          DOUBLE PRECISION NOT NULL CHECK(price > 0),
        original_price DOUBLE PRECISION CHECK(original_price IS NULL OR original_price > 0),  -- có + > price => đang sale
        stock          INTEGER NOT NULL DEFAULT 0 CHECK(stock >= 0),       -- tồn kho
        sold_count     INTEGER NOT NULL DEFAULT 0 CHECK(sold_count >= 0),  -- đã bán
        rating         DOUBLE PRECISION NOT NULL DEFAULT 5.0 CHECK(rating BETWEEN 0 AND 5),  -- = AVG(reviews.rating), trigger tự cập nhật
        review_count   INTEGER NOT NULL DEFAULT 0 CHECK(review_count >= 0),     -- = COUNT(reviews), trigger tự cập nhật
        image_url      TEXT,             -- ảnh bìa
        status         TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active', 'hidden')),
        created_at     TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at     TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    """,
    """
    CREATE TABLE product_images (
        id          SERIAL PRIMARY KEY,
        product_id  INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
        image_url   TEXT NOT NULL,
        sort_order  INTEGER NOT NULL DEFAULT 0,
        created_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    """,
    """
    CREATE TABLE cart_items (
        id         SERIAL PRIMARY KEY,
        buyer_id   INTEGER NOT NULL REFERENCES users(id),
        product_id INTEGER NOT NULL REFERENCES products(id),
        quantity   INTEGER NOT NULL DEFAULT 1 CHECK(quantity > 0),
        color      TEXT,
        size       TEXT,
        added_at   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(buyer_id, product_id, color, size)
    );
    """,
    """
    CREATE TABLE wishlist_items (
        id         SERIAL PRIMARY KEY,
        buyer_id   INTEGER NOT NULL REFERENCES users(id),
        product_id INTEGER NOT NULL REFERENCES products(id),
        added_at   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(buyer_id, product_id)
    );
    """,
    """
    CREATE TABLE addresses (
        id             SERIAL PRIMARY KEY,
        user_id        INTEGER NOT NULL REFERENCES users(id),
        label          TEXT NOT NULL,
        recipient_name TEXT NOT NULL,
        phone          TEXT NOT NULL,
        address_line   TEXT NOT NULL,
        is_default     BOOLEAN NOT NULL DEFAULT false,
        created_at     TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    """,
    """
    CREATE TABLE orders (
        id                SERIAL PRIMARY KEY,
        buyer_id          INTEGER NOT NULL REFERENCES users(id),
        recipient_name    TEXT NOT NULL,
        recipient_email   TEXT NOT NULL,
        recipient_phone   TEXT,
        shipping_address  TEXT NOT NULL,
        shipping_method   TEXT NOT NULL DEFAULT 'standard' CHECK(shipping_method IN ('standard', 'express')),
        shipping_fee      DOUBLE PRECISION NOT NULL DEFAULT 0,
        voucher_code      TEXT,
        discount_amount   DOUBLE PRECISION NOT NULL DEFAULT 0,
        total_price       DOUBLE PRECISION NOT NULL,
        -- suy ra từ order_payments + order_items.item_status, không sửa tay (xem app/routers/orders.py::_recompute_order_status)
        status            TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending', 'processing', 'shipped', 'delivered', 'cancelled')),
        created_at        TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    """,
    """
    CREATE TABLE order_items (
        id                 SERIAL PRIMARY KEY,
        order_id           INTEGER NOT NULL REFERENCES orders(id),
        product_id         INTEGER NOT NULL REFERENCES products(id),
        seller_id          INTEGER NOT NULL REFERENCES users(id),
        quantity           INTEGER NOT NULL CHECK(quantity > 0),
        color              TEXT,
        size               TEXT,
        price_at_purchase  DOUBLE PRECISION NOT NULL,
        -- do seller tự cập nhật khi đóng gói/giao hàng cho đúng phần hàng của mình
        item_status        TEXT NOT NULL DEFAULT 'processing' CHECK(item_status IN ('processing', 'shipped', 'delivered'))
    );
    """,
    # 1 dòng / seller có mặt trong đơn — buyer chuyển khoản thẳng vào QR của seller đó,
    # giao dịch "completed" khi CẢ buyer_confirmed_at và seller_confirmed_at đều có giá trị.
    """
    CREATE TABLE order_payments (
        id                   SERIAL PRIMARY KEY,
        order_id             INTEGER NOT NULL REFERENCES orders(id),
        seller_id            INTEGER NOT NULL REFERENCES users(id),
        amount               DOUBLE PRECISION NOT NULL,
        qr_image_url         TEXT,  -- chụp lại QR của seller tại thời điểm đặt hàng
        buyer_confirmed_at   TIMESTAMP,
        seller_confirmed_at  TIMESTAMP,
        status               TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending', 'completed', 'failed')),
        created_at           TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(order_id, seller_id)
    );
    """,
    """
    CREATE TABLE passport_stamps (
        user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        stamp_id   TEXT NOT NULL,                          -- id con dấu, khớp STAMPS ở script.js
        earned_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (user_id, stamp_id)
    );
    """,
    """
    CREATE TABLE notifications (
        id          SERIAL PRIMARY KEY,
        user_id     INTEGER NOT NULL REFERENCES users(id),  -- người nhận thông báo
        type        TEXT NOT NULL,
        title       TEXT NOT NULL,
        message     TEXT NOT NULL,
        order_id    INTEGER REFERENCES orders(id),
        is_read     BOOLEAN NOT NULL DEFAULT false,
        created_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    """,
    # Đánh giá bằng sao (1-5) + bình luận của buyer cho 1 sản phẩm. Mỗi buyer chỉ có
    # 1 đánh giá cho 1 sản phẩm (UNIQUE) — đánh giá lại thì cập nhật (upsert) thay vì
    # cộng dồn thêm dòng mới, tránh 1 người "spam" nhiều đánh giá cho cùng 1 món.
    """
    CREATE TABLE reviews (
        id          SERIAL PRIMARY KEY,
        product_id  INTEGER NOT NULL REFERENCES products(id),
        buyer_id    INTEGER NOT NULL REFERENCES users(id),
        rating      INTEGER NOT NULL CHECK(rating BETWEEN 1 AND 5),
        comment     TEXT,
        created_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(product_id, buyer_id)
    );
    """,
    """
    CREATE TABLE review_images (
        id         SERIAL PRIMARY KEY,
        review_id  INTEGER NOT NULL REFERENCES reviews(id) ON DELETE CASCADE,
        image_url  TEXT NOT NULL
    );
    """,
    "CREATE INDEX idx_products_seller     ON products(seller_id);",
    "CREATE INDEX idx_products_village    ON products(village_id);",
    "CREATE INDEX idx_product_images_prod ON product_images(product_id);",
    "CREATE INDEX idx_seller_profiles_v   ON seller_profiles(village_id);",
    "CREATE INDEX idx_cart_buyer          ON cart_items(buyer_id);",
    "CREATE INDEX idx_wishlist_buyer      ON wishlist_items(buyer_id);",
    "CREATE INDEX idx_addresses_user      ON addresses(user_id);",
    "CREATE INDEX idx_orders_buyer        ON orders(buyer_id);",
    "CREATE INDEX idx_order_items_order   ON order_items(order_id);",
    "CREATE INDEX idx_order_items_seller  ON order_items(seller_id);",
    "CREATE INDEX idx_order_payments_ord  ON order_payments(order_id);",
    "CREATE INDEX idx_order_payments_sel  ON order_payments(seller_id);",
    "CREATE INDEX idx_notifications_user  ON notifications(user_id);",
    "CREATE INDEX idx_reviews_product     ON reviews(product_id);",
    "CREATE INDEX idx_reviews_buyer       ON reviews(buyer_id);",
    # SQLite hỗ trợ CREATE TRIGGER ... BEGIN ... END trực tiếp; PostgreSQL bắt buộc tách
    # riêng 1 hàm PL/pgSQL rồi mới CREATE TRIGGER trỏ vào hàm đó.
    #
    # Trừ tồn kho / cộng đã bán khi 1 giao dịch thanh toán với 1 seller cụ thể "completed"
    # (cả buyer lẫn seller đều đã xác nhận) — chỉ trừ đúng các order_items của SELLER đó
    # trong đơn (1 đơn có thể có nhiều seller, mỗi seller thanh toán/giao hàng độc lập).
    """
    CREATE OR REPLACE FUNCTION fn_payment_completed_update_stock() RETURNS TRIGGER AS $$
    BEGIN
        UPDATE products
        SET sold_count = sold_count + (
                SELECT COALESCE(SUM(oi.quantity), 0) FROM order_items oi
                WHERE oi.order_id = NEW.order_id AND oi.seller_id = NEW.seller_id AND oi.product_id = products.id
            ),
            stock = GREATEST(0, stock - (
                SELECT COALESCE(SUM(oi.quantity), 0) FROM order_items oi
                WHERE oi.order_id = NEW.order_id AND oi.seller_id = NEW.seller_id AND oi.product_id = products.id
            ))
        WHERE id IN (
            SELECT product_id FROM order_items WHERE order_id = NEW.order_id AND seller_id = NEW.seller_id
        );
        RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;
    """,
    """
    CREATE TRIGGER trg_payment_completed_update_stock
    AFTER UPDATE OF status ON order_payments
    FOR EACH ROW
    WHEN (NEW.status = 'completed' AND OLD.status <> 'completed')
    EXECUTE FUNCTION fn_payment_completed_update_stock();
    """,
    # products.rating/review_count là cột "đúc sẵn" (denormalize) để trang sản phẩm đọc
    # nhanh mà không phải JOIN/AVG qua bảng reviews mỗi lần hiển thị — hàm + 3 trigger dưới
    # đây giữ chúng luôn khớp với dữ liệu thật trong reviews sau mỗi thêm/sửa/xoá đánh giá.
    """
    CREATE OR REPLACE FUNCTION fn_reviews_sync_product() RETURNS TRIGGER AS $$
    DECLARE
        pid INTEGER;
    BEGIN
        IF TG_OP = 'DELETE' THEN
            pid := OLD.product_id;
        ELSE
            pid := NEW.product_id;
        END IF;

        UPDATE products SET
            rating = COALESCE((SELECT ROUND(AVG(rating), 2) FROM reviews WHERE product_id = pid), 5.0),
            review_count = (SELECT COUNT(*) FROM reviews WHERE product_id = pid)
        WHERE id = pid;

        RETURN NULL;
    END;
    $$ LANGUAGE plpgsql;
    """,
    """
    CREATE TRIGGER trg_reviews_after_insert
    AFTER INSERT ON reviews
    FOR EACH ROW EXECUTE FUNCTION fn_reviews_sync_product();
    """,
    """
    CREATE TRIGGER trg_reviews_after_update
    AFTER UPDATE ON reviews
    FOR EACH ROW EXECUTE FUNCTION fn_reviews_sync_product();
    """,
    """
    CREATE TRIGGER trg_reviews_after_delete
    AFTER DELETE ON reviews
    FOR EACH ROW EXECUTE FUNCTION fn_reviews_sync_product();
    """,
]


# ---- dữ liệu mẫu: 13 sản phẩm gốc trên Sàn thương mại (script.js) + 11 món giá mềm, đủ 2 trang Shop ----
PROD_DIR = "assets/product_img/"
DEMO_QR = "assets/qr_code.png"

# (id_tmp, tên, làng, giá, giá gốc (None nếu không sale), tồn kho, đã bán, mô tả, ảnh,
#  chất liệu, hướng dẫn size, màu (csv), size (csv))
PRODUCTS_SEED = [
    ("am-tra", "Bộ ấm trà men hỏa biến", "bt", 1_450_000, None, 24, 0,
     "Bộ ấm trà phủ men hỏa biến xanh ngọc — sắc men biến ảo theo nhiệt độ lò nung, kèm đĩa và khay hoa xanh.",
     "Bộ Ấm Trà Đĩa Men Hỏa Biến Xanh Khay Hoa Xanh.png",
     "Gốm sứ Bát Tràng nung men hỏa biến", None, None, None),
    ("hu-tra", "Hũ đựng trà Mã Đáo Thành Công", "bt", 1_180_000, None, 18, 0,
     "Hũ sứ men xanh vẽ vàng họa tiết \"Mã Đáo Thành Công\" — biểu tượng cát tường, may mắn.",
     "Hũ Đựng Trà Men Xanh Mã Đáo Thành Công Vẽ Vàng.png",
     "Gốm sứ Bát Tràng vẽ vàng", None, None, None),
    ("dia-sen", "Đĩa trưng bày hoa sen ánh trăng", "bt", 1_350_000, None, 15, 0,
     "Đĩa trưng bày đắp nổi, vẽ màu hoa sen dưới ánh trăng — tinh xảo trong từng cánh sen.",
     "Đĩa Trưng Bày Đắp Nổi Vẽ Màu Hoa Sen Ánh Trăng.png",
     "Gốm sứ Bát Tràng đắp nổi", None, None, None),
    ("cavat-lua", "Cà vạt lụa tơ tằm", "vp", 680_000, None, 40, 0,
     "Cà vạt dệt 100% lụa tơ tằm Vạn Phúc, sắc đỏ đô sang trọng với hoa văn chìm tinh tế.",
     "CARAVAT LỤA TƠ TẰM NGHỆ NHÂN đỏ đô.png",
     "Lụa tơ tằm 100%", "Cà vạt khổ chuẩn — dài 148cm, bản to 8.5cm, phù hợp mọi vóc dáng.",
     "Đỏ đô,Xanh navy,Đen", None),
    ("khan-sen", "Khăn lụa vân sen hồng", "vp", 920_000, None, 30, 0,
     "Khăn lụa vân sen phối sắc hồng — hoa văn sen ẩn hiện khi soi nắng, dệt thủ công.",
     "Khăn lụa vân Sen hồng phối màu.png",
     "Lụa tơ tằm 100%", None, "Hồng phấn,Xanh ngọc,Vàng nhạt", None),
    ("hop-may", "Hộp đựng đồ mây tre đan", "pv", 540_000, None, 35, 0,
     "Hộp đựng đồ đan tay từ mây tre Phú Vinh theo kỹ thuật nong đôi bền chắc.",
     "Hộp đựng đồ Mây Tre Đan.png",
     "Mây tre tự nhiên", "Có 3 cỡ: Nhỏ (15cm), Vừa (20cm), Lớn (25cm) — đo theo đường kính đáy hộp.",
     None, "Nhỏ,Vừa,Lớn"),
    ("tui-may", "Túi đeo chéo mây tre đan", "pv", 750_000, None, 28, 0,
     "Túi đeo chéo đan tay phối quai mây tròn, hoa văn xương cá đặc trưng Phú Vinh.",
     "Túi Đeo Chéo Mây Tre Đan.png",
     "Mây tre tự nhiên phối da", None, "Mây tự nhiên,Mây nhuộm nâu", None),
    ("binh-loc", "Bình hút lộc Mã Đáo Thành Công", "bt", 2_200_000, None, 10, 0,
     "Bình hút lộc dáng tròn đầy, vẽ tay họa tiết \"Mã Đáo Thành Công\" trên nền men cao cấp.",
     "Bình hút lộc Bát Tràng vẽ mã đáo thành công.png",
     "Gốm sứ Bát Tràng cao cấp", None, None, None),
    ("binh-sen", "Bình sen vàng kim men xanh đồng", "bt", 2_850_000, None, 8, 0,
     "Bình cắm hoa men xanh đồng phủ vàng kim, đắp nổi hoa sen — quốc hoa của Việt Nam.",
     "Bình sen vàng kim cao cấp men xanh đồng.png",
     "Gốm sứ Bát Tràng phủ vàng kim", None, None, None),
    ("dia-bau", "Đĩa sứ bầu dục men lam", "bt", 890_000, 990_000, 22, 0,
     "Đĩa sứ dáng bầu dục vẽ men lam cổ điển — vừa để bày biện món ăn, vừa làm vật trang trí.",
     "Đĩa sứ bầu dục.png",
     "Gốm sứ Bát Tràng men lam", None, None, None),
    ("khan-nguson", "Khăn tơ ngũ sắc xanh cam", "vp", 780_000, 850_000, 26, 0,
     "Khăn tơ tằm phối ngũ sắc xanh — cam rực rỡ, dệt thủ công tại Vạn Phúc.",
     "Khăn tơ ngũ sắc xanh cam.png",
     "Tơ tằm", None, "Xanh - Cam,Hồng - Tím", None),
    ("aodai-lua", "Áo dài lụa tơ tằm Hà Đông", "vp", 3_600_000, None, 6, 0,
     "Áo dài may từ lụa tơ tằm Hà Đông nguyên tấm, hoa văn cẩm giao trang nhã.",
     "Áo dài lụa tơ tằm Hà Đông cẩm giao.png",
     "Lụa tơ tằm Hà Đông nguyên tấm",
     "Chọn size theo số đo vòng ngực: S (78-82cm), M (83-87cm), L (88-92cm), XL (93-97cm).",
     "Đỏ đô,Xanh ngọc,Vàng đồng", "S,M,L,XL"),
    ("tui-ruot-may", "Túi đan ruột mây hình chữ nhật", "pv", 690_000, None, 32, 0,
     "Túi dáng hộp chữ nhật đan từ ruột mây Phú Vinh, nan mảnh đều tăm tắp.",
     "Túi Đan ruột mây hình chữ nhật.png",
     "Ruột mây tự nhiên", None, None, None),
    # đồ dùng hằng ngày giá mềm — ảnh lấy từ Unsplash (Unsplash License, dùng thương mại miễn phí)
    ("coc-men-tro", "Cốc gốm men tro quai tròn", "bt", 95_000, None, 60, 0,
     "Cốc gốm dáng trụ, men tro xám trắng, chân để mộc — dung tích khoảng 300ml cho trà, cà phê mỗi sáng.",
     "Cốc gốm men tro quai tròn.jpg",
     "Gốm Bát Tràng men tro", None, None, None),
    ("bat-hoa-van", "Bộ 3 bát gốm vẽ hoa văn", "bt", 135_000, None, 40, 0,
     "Bộ 3 bát ăn cơm, mỗi chiếc một hoa văn: hoa nhí vàng, hoa dây hồng, ô trám xanh lam.",
     "Bộ 3 bát gốm vẽ hoa văn.jpg",
     "Gốm sứ Bát Tràng vẽ men màu", "Đường kính miệng bát khoảng 12cm, cao 6cm — 1 bộ gồm 3 chiếc.", None, None),
    ("chen-men-mau", "Chén gốm men màu nhỏ", "bt", 25_000, None, 150, 0,
     "Chén gốm nhỏ làm tay, men màu đất — dùng uống trà, đựng nước chấm, gia vị hay đồ trang sức nhỏ.",
     "Bộ chén gốm men màu.jpg",
     "Gốm Bát Tràng men màu", "Đường kính khoảng 8cm, cao 4cm — bán lẻ theo chiếc.",
     "Nâu đất,Xám tro,Trắng ngà,Vàng mật,Xanh rêu", None),
    ("lo-men-lam", "Lọ hoa gốm men lam cổ cao", "bt", 150_000, None, 25, 0,
     "Lọ hoa dáng bầu cổ cao, men lam sẫm loang nhẹ — vừa cắm một đến ba cành hoa.",
     "Lọ hoa gốm men lam cổ cao.jpg",
     "Gốm Bát Tràng men lam", "Cao khoảng 20cm, đường kính thân 8cm.", None, None),
    ("buoc-toc-lua", "Dây buộc tóc lụa", "vp", 45_000, None, 120, 0,
     "Dây buộc tóc bọc lụa mềm, lõi chun co giãn — hạn chế gãy rối tóc, may từ lụa thừa của xưởng.",
     "Dây buộc tóc lụa.jpg",
     "Lụa tơ tằm Vạn Phúc, lõi chun", None, "Hồng phấn,Xanh cổ vịt,Xanh bạc hà,Tím oải hương", None),
    ("khan-in-hoa", "Khăn lụa dài in hoa văn", "vp", 165_000, None, 45, 0,
     "Khăn lụa dài in hoa văn nhiều màu, mỏng nhẹ, rủ mềm — quàng cổ hay choàng vai đều đẹp.",
     "Khăn lụa dài in hoa văn.jpg",
     "Lụa Vạn Phúc in hoa", "Khổ khăn 50 x 170cm.", "Hồng tím,Xanh ngọc,Cam đỏ", None),
    ("lua-tron-nga", "Lụa trơn màu ngà (bán theo mét)", "vp", 210_000, None, 80, 0,
     "Lụa trơn màu ngà dệt tại Vạn Phúc, khổ 90cm, bán theo mét — may áo, váy, khăn, vỏ gối.",
     "Lụa tơ tằm trơn màu ngà.jpg",
     "Lụa tơ tằm Vạn Phúc dệt trơn",
     "Khổ vải 90cm. Số lượng = số mét vải (vd. chọn 2 là 2 mét). Áo sơ mi cần khoảng 1,8 - 2m.", None, None),
    ("lot-ly-may", "Lót ly mây đan tròn", "pv", 25_000, None, 150, 0,
     "Lót ly đan tay hình tròn, viền mây quấn chặt — bảo vệ mặt bàn khỏi vết nước và nhiệt.",
     "Lót ly mây đan tròn.jpg",
     "Mây tự nhiên", "Đường kính khoảng 11cm — bán lẻ theo chiếc.", None, None),
    ("gio-quai-xach", "Giỏ mây đan quai xách", "pv", 120_000, None, 35, 0,
     "Giỏ mây đan tay dáng thuyền, quai cong cao — đựng hoa quả, bánh mì, đi chợ hay picnic.",
     "Giỏ mây đan quai xách.jpg",
     "Mây nhuộm nâu", "Dài khoảng 30cm, cao cả quai 28cm.", None, None),
    ("khay-may-tron", "Khay mây đan tròn có quai", "pv", 180_000, None, 25, 0,
     "Khay mây đan tròn hai quai cầm — bưng bữa sáng, bày ấm chén hay gom gọn đồ trên bàn.",
     "Khay mây đan tròn có quai.jpg",
     "Mây tự nhiên", "Đường kính khoảng 35cm, thành cao 5cm.", None, None),
    ("quat-la-co", "Quạt lá cọ đan tay", "pv", 35_000, None, 80, 0,
     "Quạt lá cọ phơi khô, cán tre nhỏ gọn — quạt mát ngày hè hoặc treo tường trang trí.",
     "Quạt lá cọ đan tay.jpg",
     "Lá cọ phơi khô, cán tre", None, None, None),
]

VILLAGES_SEED = [
    ("bt", "Bát Tràng", "Gốm sứ", "Nơi đất và lửa kết tinh thành những tác phẩm vượt thời gian."),
    ("vp", "Vạn Phúc", "Lụa tơ tằm", "Mềm mại như dòng chảy thời gian, lưu giữ vẻ đẹp trong từng sợi lụa."),
    ("pv", "Phú Vinh", "Mây tre đan", "Từ tre mây bình dị nên những sản phẩm đậm hồn Việt."),
]

# tên, username, email, sđt, mật khẩu demo, tên gian hàng, làng nghề, giới thiệu
SELLERS_SEED = [
    ("Trần Văn Minh", "minh", "tranvanminh.battrang@kimvie.vn", "0912345678", "demo123",
     "Gốm Minh Long Bát Tràng", "bt", "Ba đời làm gốm tại Bát Tràng, chuyên men hỏa biến và men lam cổ."),
    ("Nguyễn Thị Hoa", "hoa", "nguyenthihoa.vanphuc@kimvie.vn", "0987654321", "demo123",
     "Lụa Hoa Vạn Phúc", "vp", "Xưởng dệt lụa tơ tằm gia truyền, giữ nghề ươm tơ dệt lụa hơn 20 năm."),
    ("Lê Văn Phú", "phu", "levanphu.phuvinh@kimvie.vn", "0909112233", "demo123",
     "Mây Tre Phú An", "pv", "Chuyên đan mây tre thủ công, sản phẩm đã xử lý chống mối mọt."),
]

# tên, username, email, sđt, mật khẩu demo
BUYERS_SEED = [
    ("Phạm Thị Lan", "lan", "phamthilan@gmail.com", "0933112244", "demo123"),
    ("Đỗ Minh Khang", "khang", "dominhkhang@gmail.com", "0977889900", "demo123"),
]

def seed_data(conn: psycopg.Connection):
    cur = conn.cursor()

    village_id = {}
    for code, name, craft, desc in VILLAGES_SEED:
        cur.execute(
            "INSERT INTO villages (code, name, craft, description) VALUES (%s, %s, %s, %s) RETURNING id",
            (code, name, craft, desc),
        )
        village_id[code] = cur.fetchone()[0]

    seller_user_id = {}
    for name, username, email, phone, pw, shop_name, v_code, bio in SELLERS_SEED:
        cur.execute(
            "INSERT INTO users (name, username, email, phone, password_hash, is_seller) VALUES (%s, %s, %s, %s, %s, 1) RETURNING id",
            (name, username, email, phone, hash_password(pw)),
        )
        uid = cur.fetchone()[0]
        seller_user_id[v_code] = uid
        cur.execute(
            "INSERT INTO seller_profiles (user_id, shop_name, village_id, phone, bio, payment_qr_url) VALUES (%s, %s, %s, %s, %s, %s)",
            (uid, shop_name, village_id[v_code], phone, bio, DEMO_QR),
        )

    buyer_user_id = []
    for name, username, email, phone, pw in BUYERS_SEED:
        cur.execute(
            "INSERT INTO users (name, username, email, phone, password_hash, is_seller) VALUES (%s, %s, %s, %s, %s, 0) RETURNING id",
            (name, username, email, phone, hash_password(pw)),
        )
        buyer_user_id.append(cur.fetchone()[0])

    lan_id, khang_id = buyer_user_id

    # 1 địa chỉ mặc định mỗi buyer, dùng luôn cho đơn mẫu bên dưới
    cur.execute(
        "INSERT INTO addresses (user_id, label, recipient_name, phone, address_line, is_default) VALUES (%s, %s, %s, %s, %s, true)",
        (lan_id, "Nhà riêng", "Phạm Thị Lan", "0933112244", "45 Trần Hưng Đạo, P. Cầu Kho, TP. Hồ Chí Minh"),
    )
    cur.execute(
        "INSERT INTO addresses (user_id, label, recipient_name, phone, address_line, is_default) VALUES (%s, %s, %s, %s, %s, true)",
        (khang_id, "Nhà riêng", "Đỗ Minh Khang", "0977889900", "12 Nguyễn Trãi, P. Bến Thành, TP. Hồ Chí Minh"),
    )

    product_id = {}
    for pid, name, v_code, price, orig, stock, sold, desc, img, material, size_guide, colors, sizes in PRODUCTS_SEED:
        content = PRODUCT_CONTENT.get(name, {})
        cur.execute(
            """INSERT INTO products
               (seller_id, village_id, name, description, story, material, size_guide, colors, sizes,
                price, original_price, stock, sold_count, image_url)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id""",
            (seller_user_id[v_code], village_id[v_code], name, content.get("description", desc), content.get("story"),
             material, size_guide, colors, sizes,
             price, orig, stock, sold, PROD_DIR + img),
        )
        product_id[pid] = cur.fetchone()[0]

    # yêu thích mẫu — Phạm Thị Lan đã lưu 2 món để mua sau
    cur.execute("INSERT INTO wishlist_items (buyer_id, product_id) VALUES (%s, %s)", (lan_id, product_id["aodai-lua"]))
    cur.execute("INSERT INTO wishlist_items (buyer_id, product_id) VALUES (%s, %s)", (lan_id, product_id["binh-sen"]))

    # không seed đánh giá / số "đã bán" ảo — mọi đánh giá và lượt bán đều phải đến từ
    # người mua thật (bảng reviews + trigger, order_payments completed + trigger)

    # giỏ hàng mẫu — Phạm Thị Lan đang xem 2 món
    cur.execute("INSERT INTO cart_items (buyer_id, product_id, quantity) VALUES (%s, %s, 1)",
                (lan_id, product_id["am-tra"]))
    cur.execute("INSERT INTO cart_items (buyer_id, product_id, quantity) VALUES (%s, %s, 2)",
                (lan_id, product_id["khan-sen"]))

    # không seed đơn hàng demo — mọi đơn hàng (và lượt "đã bán") đều phải do người mua thật đặt


def create_database(database_url=None):
    url = database_url or DATABASE_URL
    if not url:
        raise RuntimeError(
            "Chưa đặt KV_DATABASE_URL — xem .env.example để biết cách lấy chuỗi kết nối "
            "PostgreSQL từ Render rồi đặt vào file .env."
        )
    conn = psycopg.connect(url)
    try:
        cur = conn.cursor()
        for stmt in DROP_TABLES_SQL:
            cur.execute(stmt)
        for stmt in CREATE_TABLES_SQL:
            cur.execute(stmt)
        seed_data(conn)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
    print(f"Created database schema + seed data at: {url.split('@')[-1]}")


if __name__ == "__main__":
    create_database()
