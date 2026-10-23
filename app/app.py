"""KIMVIE backend — FastAPI phục vụ REST API (đọc/ghi thẳng vào PostgreSQL) và,
khi tìm thấy repo frontend cạnh bên, mount luôn trang web tĩnh để 1 lệnh
`uvicorn app.app:app` là chạy được cả web lẫn API trên cùng 1 origin (khỏi lo CORS)."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import FRONTEND_DIR
from app.database import db_session
from app.product_content import PRODUCT_CONTENT
from app.routers import addresses, auth, cart, notifications, orders, passport, products, reviews, seller, villages, wishlist

app = FastAPI(
    title="KIMVIE API",
    description="Backend cho website KIMVIE — sản phẩm, gian hàng người bán, giỏ hàng, đơn hàng.",
    version="1.0.0",
)

# Cho phép gọi API từ origin khác lúc dev (vd. mở frontend bằng live-server/http.server
# ở cổng riêng thay vì qua chính server này). Siết lại allow_origins khi deploy thật.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(villages.router)
app.include_router(products.router)
app.include_router(seller.router)
app.include_router(cart.router)
app.include_router(orders.router)
app.include_router(reviews.router)
app.include_router(reviews.me_router)
app.include_router(wishlist.router)
app.include_router(addresses.router)
app.include_router(notifications.router)
app.include_router(passport.router)


@app.get("/api/health")
def health():
    try:
        with db_session() as conn:
            conn.execute("SELECT 1")
        return {"status": "ok", "database": "connected"}
    except Exception as exc:
        return {"status": "error", "database": f"unreachable: {exc}"}


@app.on_event("startup")
def check_database():
    try:
        with db_session() as conn:
            rows = conn.execute(
                "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
            ).fetchall()
    except Exception as exc:
        raise RuntimeError(
            f"Không kết nối được PostgreSQL: {exc}. Kiểm tra lại biến môi trường KV_DATABASE_URL."
        ) from exc

    # kiểm tra nhanh bảng cốt lõi đã tồn tại, tránh chạy nhầm với database rỗng/khác schema
    tables = {r["table_name"] for r in rows}
    required = {
        "users", "products", "villages", "seller_profiles", "orders", "order_items", "cart_items", "reviews",
        "product_images", "review_images", "wishlist_items", "addresses", "order_payments", "notifications",
    }
    missing = required - tables
    if missing:
        raise RuntimeError(
            f"Database thiếu bảng {missing} — chạy `python create_db.py` để tạo + seed theo schema mới nhất."
        )

    # bảng hộ chiếu di sản thêm sau — tự tạo nếu chưa có để khỏi phải seed lại (create_db.py xoá sạch dữ liệu)
    with db_session() as conn:
        conn.execute(passport.CREATE_TABLE_SQL)
        # cột câu chuyện sản phẩm thêm sau + điền mô tả/câu chuyện cho các sản phẩm mẫu chưa có
        # (chỉ khi story còn trống, không ghi đè nội dung người bán đã tự viết)
        conn.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS story TEXT")
        for name, content in PRODUCT_CONTENT.items():
            conn.execute(
                "UPDATE products SET description = %s, story = %s WHERE name = %s AND story IS NULL",
                (content["description"], content["story"], name),
            )


# ---- mount frontend tĩnh (index.html/script.js/styles.css/assets/...) nếu tìm thấy ----
_frontend = Path(FRONTEND_DIR)
if _frontend.is_dir() and (_frontend / "index.html").is_file():
    app.mount("/", StaticFiles(directory=str(_frontend), html=True), name="frontend")
