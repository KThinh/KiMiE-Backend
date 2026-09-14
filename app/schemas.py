"""Pydantic models — request/response cho API. Đặt tên khớp với field trên giao
diện web (vd. spName/spVillage/spPrice/spStock trên form đăng sản phẩm) để dễ đối
chiếu khi nối với script.js."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


# ---------- auth / users ----------

class UserRegisterIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    phone: Optional[str] = None
    password: str = Field(min_length=6, max_length=200)


class UserLoginIn(BaseModel):
    email: EmailStr
    password: str


class SellerProfileOut(BaseModel):
    shop_name: str
    village_code: str
    village_name: str
    phone: Optional[str] = None
    bio: Optional[str] = None


class UserOut(BaseModel):
    id: int
    name: str
    email: str
    phone: Optional[str] = None
    is_seller: bool
    created_at: str
    seller: Optional[SellerProfileOut] = None


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class SellerRegisterIn(BaseModel):
    shop_name: str = Field(min_length=1, max_length=160)
    village_code: str
    phone: str = Field(min_length=1, max_length=30)
    bio: Optional[str] = None


# ---------- villages ----------

class VillageOut(BaseModel):
    id: int
    code: str
    name: str
    craft: str
    description: Optional[str] = None


# ---------- products ----------

class ProductIn(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    village_code: str
    price: float = Field(gt=0)
    stock: int = Field(ge=0)
    description: Optional[str] = None
    image_url: Optional[str] = None  # URL bình thường hoặc data: URI (ảnh đã nén ở frontend)


class ProductUpdateIn(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    village_code: Optional[str] = None
    price: Optional[float] = Field(default=None, gt=0)
    stock: Optional[int] = Field(default=None, ge=0)
    description: Optional[str] = None
    image_url: Optional[str] = None
    status: Optional[str] = None  # 'active' | 'hidden'


class ProductOut(BaseModel):
    id: int
    seller_id: int
    shop_name: str
    village_code: str
    village_name: str
    name: str
    description: Optional[str] = None
    price: float
    stock: int
    sold_count: int
    rating: float
    review_count: int
    image_url: Optional[str] = None
    status: str
    created_at: str
    updated_at: str


class ProductListOut(BaseModel):
    total: int
    page: int
    per_page: int
    items: list[ProductOut]


# ---------- seller dashboard ----------

class SellerStatsOut(BaseModel):
    total_products: int
    in_stock: int
    out_of_stock: int
    inventory_value: float
    total_sold: int
    total_revenue: float


# ---------- cart ----------

class CartItemIn(BaseModel):
    product_id: int
    quantity: int = Field(gt=0, default=1)


class CartItemOut(BaseModel):
    id: int
    product: ProductOut
    quantity: int
    line_total: float


class CartOut(BaseModel):
    items: list[CartItemOut]
    subtotal: float


# ---------- orders ----------

class OrderItemIn(BaseModel):
    product_id: int
    quantity: int = Field(gt=0)


class OrderCreateIn(BaseModel):
    recipient_name: str = Field(min_length=1, max_length=160)
    recipient_email: EmailStr
    recipient_phone: Optional[str] = None
    shipping_address: str = Field(min_length=1, max_length=400)
    voucher_code: Optional[str] = None
    items: list[OrderItemIn] = Field(min_length=1)


class OrderItemOut(BaseModel):
    product_id: int
    product_name: str
    seller_id: int
    quantity: int
    price_at_purchase: float


class OrderOut(BaseModel):
    id: int
    status: str
    voucher_code: Optional[str] = None
    discount_amount: float
    total_price: float
    recipient_name: str
    recipient_email: str
    recipient_phone: Optional[str] = None
    shipping_address: str
    created_at: str
    items: list[OrderItemOut]


# ---------- reviews (đánh giá sao + bình luận) ----------

class ReviewIn(BaseModel):
    rating: int = Field(ge=1, le=5)
    comment: Optional[str] = Field(default=None, max_length=2000)


class ReviewOut(BaseModel):
    id: int
    product_id: int
    buyer_id: int
    buyer_name: str
    rating: int
    comment: Optional[str] = None
    created_at: str
    updated_at: str


class ReviewListOut(BaseModel):
    average_rating: float
    review_count: int
    items: list[ReviewOut]
    my_review: Optional[ReviewOut] = None
