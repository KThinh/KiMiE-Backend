"""
Tạo file database.db (SQLite) theo đúng cấu trúc mô tả trong database-schema.md,
đồng thời chèn sẵn dữ liệu mẫu lấy từ chính giao diện trang web (13 sản phẩm thật
trong script.js, 3 làng nghề, người bán/người mua mẫu) để file .db dùng được ngay
cho việc demo/truy vấn thử — không phải bảng rỗng.

Cách dùng:
    python create_db.py
"""

import hashlib
import sqlite3

DB_PATH = "database.db"

# xoá & tạo lại từ đầu mỗi lần chạy để đảm bảo schema + dữ liệu luôn khớp với file mới nhất
CREATE_TABLES_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE villages (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    code        TEXT NOT NULL UNIQUE CHECK(code IN ('bt', 'vp', 'pv')),
    name        TEXT NOT NULL,
    craft       TEXT NOT NULL,
    description TEXT
);

CREATE TABLE users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT NOT NULL,
    email         TEXT NOT NULL UNIQUE,
    phone         TEXT,
    password_hash TEXT NOT NULL,
    is_seller     INTEGER NOT NULL DEFAULT 0 CHECK(is_seller IN (0, 1)),
    created_at    DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE seller_profiles (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL UNIQUE REFERENCES users(id),
    shop_name  TEXT NOT NULL,
    village_id INTEGER NOT NULL REFERENCES villages(id),
    phone      TEXT,
    bio        TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE products (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    seller_id   INTEGER NOT NULL REFERENCES users(id),
    village_id  INTEGER NOT NULL REFERENCES villages(id),
    name        TEXT NOT NULL,
    description TEXT,
    price       REAL NOT NULL CHECK(price > 0),
    stock       INTEGER NOT NULL DEFAULT 0 CHECK(stock >= 0),       -- tồn kho
    sold_count  INTEGER NOT NULL DEFAULT 0 CHECK(sold_count >= 0),  -- đã bán
    rating      REAL NOT NULL DEFAULT 5.0 CHECK(rating BETWEEN 0 AND 5),
    image_url   TEXT,
    status      TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active', 'hidden')),
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE cart_items (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    buyer_id   INTEGER NOT NULL REFERENCES users(id),
    product_id INTEGER NOT NULL REFERENCES products(id),
    quantity   INTEGER NOT NULL DEFAULT 1 CHECK(quantity > 0),
    added_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(buyer_id, product_id)
);

CREATE TABLE orders (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    buyer_id          INTEGER NOT NULL REFERENCES users(id),
    recipient_name    TEXT NOT NULL,
    recipient_email   TEXT NOT NULL,
    recipient_phone   TEXT,
    shipping_address  TEXT NOT NULL,
    voucher_code      TEXT,
    discount_amount   REAL NOT NULL DEFAULT 0,
    total_price       REAL NOT NULL,
    status            TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending', 'completed', 'cancelled')),
    created_at        DATETIME DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE order_items (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id           INTEGER NOT NULL REFERENCES orders(id),
    product_id         INTEGER NOT NULL REFERENCES products(id),
    seller_id          INTEGER NOT NULL REFERENCES users(id),
    quantity           INTEGER NOT NULL CHECK(quantity > 0),
    price_at_purchase  REAL NOT NULL
);

CREATE INDEX idx_products_seller     ON products(seller_id);
CREATE INDEX idx_products_village    ON products(village_id);
CREATE INDEX idx_seller_profiles_v   ON seller_profiles(village_id);
CREATE INDEX idx_cart_buyer          ON cart_items(buyer_id);
CREATE INDEX idx_orders_buyer        ON orders(buyer_id);
CREATE INDEX idx_order_items_order   ON order_items(order_id);
CREATE INDEX idx_order_items_seller  ON order_items(seller_id);

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
"""


def hash_password(plain: str) -> str:
    """Chỉ demo: băm SHA-256. Khi build backend thật PHẢI thay bằng bcrypt/argon2
    (có salt riêng từng user) — SHA-256 trần không an toàn cho mật khẩu thật."""
    return hashlib.sha256(plain.encode("utf-8")).hexdigest()


# ---- dữ liệu mẫu: 13 sản phẩm thật đang hiển thị trên Sàn thương mại (script.js) ----
PROD_DIR = "assets/product_img/"
PRODUCTS_SEED = [
    # (id_tmp, tên, làng, giá, tồn kho, đã bán, mô tả, ảnh)
    ("am-tra", "Bộ ấm trà men hỏa biến", "bt", 1_450_000, 24, 980,
     "Bộ ấm trà phủ men hỏa biến xanh ngọc — sắc men biến ảo theo nhiệt độ lò nung, kèm đĩa và khay hoa xanh.",
     "Bộ Ấm Trà Đĩa Men Hỏa Biến Xanh Khay Hoa Xanh.png"),
    ("hu-tra", "Hũ đựng trà Mã Đáo Thành Công", "bt", 1_180_000, 18, 1100,
     "Hũ sứ men xanh vẽ vàng họa tiết \"Mã Đáo Thành Công\" — biểu tượng cát tường, may mắn.",
     "Hũ Đựng Trà Men Xanh Mã Đáo Thành Công Vẽ Vàng.png"),
    ("dia-sen", "Đĩa trưng bày hoa sen ánh trăng", "bt", 1_350_000, 15, 640,
     "Đĩa trưng bày đắp nổi, vẽ màu hoa sen dưới ánh trăng — tinh xảo trong từng cánh sen.",
     "Đĩa Trưng Bày Đắp Nổi Vẽ Màu Hoa Sen Ánh Trăng.png"),
    ("cavat-lua", "Cà vạt lụa tơ tằm", "vp", 680_000, 40, 2300,
     "Cà vạt dệt 100% lụa tơ tằm Vạn Phúc, sắc đỏ đô sang trọng với hoa văn chìm tinh tế.",
     "CARAVAT LỤA TƠ TẰM NGHỆ NHÂN đỏ đô.png"),
    ("khan-sen", "Khăn lụa vân sen hồng", "vp", 920_000, 30, 1700,
     "Khăn lụa vân sen phối sắc hồng — hoa văn sen ẩn hiện khi soi nắng, dệt thủ công.",
     "Khăn lụa vân Sen hồng phối màu.png"),
    ("hop-may", "Hộp đựng đồ mây tre đan", "pv", 540_000, 35, 860,
     "Hộp đựng đồ đan tay từ mây tre Phú Vinh theo kỹ thuật nong đôi bền chắc.",
     "Hộp đựng đồ Mây Tre Đan.png"),
    ("tui-may", "Túi đeo chéo mây tre đan", "pv", 750_000, 28, 1400,
     "Túi đeo chéo đan tay phối quai mây tròn, hoa văn xương cá đặc trưng Phú Vinh.",
     "Túi Đeo Chéo Mây Tre Đan.png"),
    ("binh-loc", "Bình hút lộc Mã Đáo Thành Công", "bt", 2_200_000, 10, 420,
     "Bình hút lộc dáng tròn đầy, vẽ tay họa tiết \"Mã Đáo Thành Công\" trên nền men cao cấp.",
     "Bình hút lộc Bát Tràng vẽ mã đáo thành công.png"),
    ("binh-sen", "Bình sen vàng kim men xanh đồng", "bt", 2_850_000, 8, 260,
     "Bình cắm hoa men xanh đồng phủ vàng kim, đắp nổi hoa sen — quốc hoa của Việt Nam.",
     "Bình sen vàng kim cao cấp men xanh đồng.png"),
    ("dia-bau", "Đĩa sứ bầu dục men lam", "bt", 890_000, 22, 730,
     "Đĩa sứ dáng bầu dục vẽ men lam cổ điển — vừa để bày biện món ăn, vừa làm vật trang trí.",
     "Đĩa sứ bầu dục.png"),
    ("khan-nguson", "Khăn tơ ngũ sắc xanh cam", "vp", 780_000, 26, 1200,
     "Khăn tơ tằm phối ngũ sắc xanh — cam rực rỡ, dệt thủ công tại Vạn Phúc.",
     "Khăn tơ ngũ sắc xanh cam.png"),
    ("aodai-lua", "Áo dài lụa tơ tằm Hà Đông", "vp", 3_600_000, 6, 180,
     "Áo dài may từ lụa tơ tằm Hà Đông nguyên tấm, hoa văn cẩm giao trang nhã.",
     "Áo dài lụa tơ tằm Hà Đông cẩm giao.png"),
    ("tui-ruot-may", "Túi đan ruột mây hình chữ nhật", "pv", 690_000, 32, 540,
     "Túi dáng hộp chữ nhật đan từ ruột mây Phú Vinh, nan mảnh đều tăm tắp.",
     "Túi Đan ruột mây hình chữ nhật.png"),
]

VILLAGES_SEED = [
    ("bt", "Bát Tràng", "Gốm sứ", "Nơi đất và lửa kết tinh thành những tác phẩm vượt thời gian."),
    ("vp", "Vạn Phúc", "Lụa tơ tằm", "Mềm mại như dòng chảy thời gian, lưu giữ vẻ đẹp trong từng sợi lụa."),
    ("pv", "Phú Vinh", "Mây tre đan", "Từ tre mây bình dị nên những sản phẩm đậm hồn Việt."),
]

SELLERS_SEED = [
    # tên, email, sđt, mật khẩu demo, tên gian hàng, làng nghề, giới thiệu
    ("Trần Văn Minh", "tranvanminh.battrang@kimvie.vn", "0912345678", "demo123",
     "Gốm Minh Long Bát Tràng", "bt", "Ba đời làm gốm tại Bát Tràng, chuyên men hỏa biến và men lam cổ."),
    ("Nguyễn Thị Hoa", "nguyenthihoa.vanphuc@kimvie.vn", "0987654321", "demo123",
     "Lụa Hoa Vạn Phúc", "vp", "Xưởng dệt lụa tơ tằm gia truyền, giữ nghề ươm tơ dệt lụa hơn 20 năm."),
    ("Lê Văn Phú", "levanphu.phuvinh@kimvie.vn", "0909112233", "demo123",
     "Mây Tre Phú An", "pv", "Chuyên đan mây tre thủ công, sản phẩm đã xử lý chống mối mọt."),
]

BUYERS_SEED = [
    ("Phạm Thị Lan", "phamthilan@gmail.com", "0933112244", "demo123"),
    ("Đỗ Minh Khang", "dominhkhang@gmail.com", "0977889900", "demo123"),
]


def seed_data(conn: sqlite3.Connection):
    cur = conn.cursor()

    village_id = {}
    for code, name, craft, desc in VILLAGES_SEED:
        cur.execute(
            "INSERT INTO villages (code, name, craft, description) VALUES (?, ?, ?, ?)",
            (code, name, craft, desc),
        )
        village_id[code] = cur.lastrowid

    seller_user_id = {}
    for name, email, phone, pw, shop_name, v_code, bio in SELLERS_SEED:
        cur.execute(
            "INSERT INTO users (name, email, phone, password_hash, is_seller) VALUES (?, ?, ?, ?, 1)",
            (name, email, phone, hash_password(pw)),
        )
        uid = cur.lastrowid
        seller_user_id[v_code] = uid
        cur.execute(
            "INSERT INTO seller_profiles (user_id, shop_name, village_id, phone, bio) VALUES (?, ?, ?, ?, ?)",
            (uid, shop_name, village_id[v_code], phone, bio),
        )

    buyer_user_id = []
    for name, email, phone, pw in BUYERS_SEED:
        cur.execute(
            "INSERT INTO users (name, email, phone, password_hash, is_seller) VALUES (?, ?, ?, ?, 0)",
            (name, email, phone, hash_password(pw)),
        )
        buyer_user_id.append(cur.lastrowid)

    product_id = {}
    for pid, name, v_code, price, stock, sold, desc, img in PRODUCTS_SEED:
        cur.execute(
            """INSERT INTO products
               (seller_id, village_id, name, description, price, stock, sold_count, rating, image_url)
               VALUES (?, ?, ?, ?, ?, ?, ?, 4.9, ?)""",
            (seller_user_id[v_code], village_id[v_code], name, desc, price, stock, sold, PROD_DIR + img),
        )
        product_id[pid] = cur.lastrowid

    # giỏ hàng mẫu — Phạm Thị Lan đang xem 2 món
    lan_id = buyer_user_id[0]
    cur.execute("INSERT INTO cart_items (buyer_id, product_id, quantity) VALUES (?, ?, 1)",
                (lan_id, product_id["am-tra"]))
    cur.execute("INSERT INTO cart_items (buyer_id, product_id, quantity) VALUES (?, ?, 2)",
                (lan_id, product_id["khan-sen"]))

    # đơn hàng mẫu — Đỗ Minh Khang đặt 2 sản phẩm, áp voucher GIULUA10 (giảm 10%)
    khang_id = buyer_user_id[1]
    items = [("cavat-lua", 1), ("hop-may", 2)]
    subtotal = sum(next(p[3] for p in PRODUCTS_SEED if p[0] == pid) * qty for pid, qty in items)
    discount = round(subtotal * 0.10)
    cur.execute(
        """INSERT INTO orders
           (buyer_id, recipient_name, recipient_email, recipient_phone, shipping_address,
            voucher_code, discount_amount, total_price, status)
           VALUES (?, ?, ?, ?, ?, 'GIULUA10', ?, ?, 'pending')""",
        (khang_id, "Đỗ Minh Khang", "dominhkhang@gmail.com", "0977889900",
         "12 Nguyễn Trãi, P. Bến Thành, TP. Hồ Chí Minh", discount, subtotal - discount),
    )
    order_id = cur.lastrowid
    for pid, qty in items:
        price = next(p[3] for p in PRODUCTS_SEED if p[0] == pid)
        v_code = next(p[2] for p in PRODUCTS_SEED if p[0] == pid)
        cur.execute(
            "INSERT INTO order_items (order_id, product_id, seller_id, quantity, price_at_purchase) VALUES (?, ?, ?, ?, ?)",
            (order_id, product_id[pid], seller_user_id[v_code], qty, price),
        )

    # xác nhận đơn đã thanh toán → trigger tự cộng sold_count / trừ stock cho 2 sản phẩm trên
    cur.execute("UPDATE orders SET status = 'completed' WHERE id = ?", (order_id,))


def create_database(db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.executescript(CREATE_TABLES_SQL)
    seed_data(conn)
    conn.commit()
    conn.close()
    print(f"Created database: {db_path}")


if __name__ == "__main__":
    create_database()
