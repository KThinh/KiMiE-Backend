"""KIMVIE backend — FastAPI phục vụ REST API (đọc/ghi thẳng vào PostgreSQL) và,
khi tìm thấy repo frontend cạnh bên, mount luôn trang web tĩnh để 1 lệnh
`uvicorn app.app:app` là chạy được cả web lẫn API trên cùng 1 origin (khỏi lo CORS)."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import FRONTEND_DIR
from app.database import db_session
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
    required = {"users", "products", "villages", "seller_profiles", "orders", "order_items", "cart_items", "reviews"}
    missing = required - tables
    if missing:
        raise RuntimeError(
            f"Database thiếu bảng {missing} — chạy `python create_db.py` để tạo + seed theo schema mới nhất."
        )


# ---- mount frontend tĩnh (index.html/script.js/styles.css/assets/...) nếu tìm thấy ----
_frontend = Path(FRONTEND_DIR)
if _frontend.is_dir() and (_frontend / "index.html").is_file():
    app.mount("/", StaticFiles(directory=str(_frontend), html=True), name="frontend")
