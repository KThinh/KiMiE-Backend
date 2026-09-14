"""KIMVIE backend — FastAPI phục vụ REST API (đọc/ghi thẳng vào database.db) và,
khi tìm thấy repo frontend cạnh bên, mount luôn trang web tĩnh để 1 lệnh
`uvicorn app.main:app` là chạy được cả web lẫn API trên cùng 1 origin (khỏi lo CORS)."""

import os
import sqlite3
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import DB_PATH, FRONTEND_DIR
from app.routers import auth, cart, orders, products, reviews, seller, villages

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


@app.get("/api/health")
def health():
    db_exists = os.path.isfile(DB_PATH)
    return {"status": "ok", "database": DB_PATH, "database_exists": db_exists}


@app.on_event("startup")
def check_database():
    if not os.path.isfile(DB_PATH):
        raise RuntimeError(
            f"Không tìm thấy database tại '{DB_PATH}'. Chạy `python create_db.py` ở thư mục gốc "
            "backend trước để tạo + seed database.db, rồi khởi động lại server."
        )
    # kiểm tra nhanh bảng cốt lõi đã tồn tại, tránh chạy nhầm với file .db cũ/khác schema
    conn = sqlite3.connect(DB_PATH)
    tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    conn.close()
    required = {"users", "products", "villages", "seller_profiles", "orders", "order_items", "cart_items", "reviews"}
    missing = required - tables
    if missing:
        raise RuntimeError(
            f"database.db thiếu bảng {missing} — có vẻ là file .db cũ. Xoá file và chạy lại "
            "`python create_db.py` để tạo theo schema mới nhất."
        )


# ---- mount frontend tĩnh (index.html/script.js/styles.css/assets/...) nếu tìm thấy ----
_frontend = Path(FRONTEND_DIR)
if _frontend.is_dir() and (_frontend / "index.html").is_file():
    app.mount("/", StaticFiles(directory=str(_frontend), html=True), name="frontend")
