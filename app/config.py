"""Cấu hình đọc từ biến môi trường (có .env.example làm mẫu), có giá trị mặc định
để chạy demo ngay không cần setup gì thêm."""

import os
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BACKEND_DIR / ".env")  # không lỗi nếu file .env không tồn tại

# đường dẫn file SQLite — mặc định nằm cạnh create_db.py ở gốc repo backend
DB_PATH = os.environ.get("KV_DB_PATH", str(BACKEND_DIR / "database.db"))

# thư mục chứa mã nguồn frontend (repo KiMViE-Website) để mount làm static site —
# mặc định giả sử 2 repo nằm cạnh nhau: .../Github/KiMiE-Backend và .../Github/KiMViE-Website
FRONTEND_DIR = os.environ.get("KV_FRONTEND_DIR", str(BACKEND_DIR.parent / "KiMViE-Website"))

# khoá ký JWT — BẮT BUỘC đặt biến môi trường KV_JWT_SECRET riêng khi deploy thật.
# Giá trị mặc định chỉ để chạy demo trên máy cá nhân.
JWT_SECRET = os.environ.get("KV_JWT_SECRET", "kimvie-dev-secret-doi-truoc-khi-deploy-that")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("KV_TOKEN_EXPIRE_MINUTES", 60 * 24 * 7))  # 7 ngày, tiện demo

if JWT_SECRET.startswith("kimvie-dev-secret"):
    import warnings
    warnings.warn(
        "KV_JWT_SECRET chưa được đặt — đang dùng khoá mặc định CHỈ DÀNH CHO DEMO. "
        "Đặt biến môi trường KV_JWT_SECRET trước khi deploy thật.",
        stacklevel=2,
    )
