"""Pydantic models — request/response cho API. Đặt tên khớp với field trên giao
diện web (vd. spName/spVillage/spPrice/spStock trên form đăng sản phẩm) để dễ đối
chiếu khi nối với script.js."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


# ---------- auth / users ----------

class UserRegisterIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    username: str = Field(min_length=3, max_length=40, pattern=r"^[a-zA-Z0-9_.]+$")
    email: EmailStr
    phone: Optional[str] = None
    password: str = Field(min_length=6, max_length=200)


class UserLoginIn(BaseModel):
    username: str
    password: str


class UserUpdateIn(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    avatar_url: Optional[str] = None


class ChangePasswordIn(BaseModel):
    current_password: str
    new_password: str = Field(min_length=6, max_length=200)


class SellerProfileOut(BaseModel):
    shop_name: str
    village_code: str
    village_name: str
    phone: Optional[str] = None
    bio: Optional[str] = None
    payment_qr_url: Optional[str] = None


class UserOut(BaseModel):
    id: int
    name: str
    username: str
    email: str
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    is_seller: bool
    created_at: datetime
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
    payment_qr_url: Optional[str] = None  # ảnh QR nhận tiền của gian hàng (data URI hoặc URL)


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
    original_price: Optional[float] = Field(default=None, gt=0)  # có giá này + > price => đang sale
    stock: int = Field(ge=0)
    description: Optional[str] = None
    material: Optional[str] = None
    size_guide: Optional[str] = None
    colors: Optional[str] = None  # danh sách phân cách bởi dấu phẩy, vd "Xanh,Đỏ,Vàng"
    sizes: Optional[str] = None
    image_url: Optional[str] = None  # ảnh bìa — URL bình thường hoặc data: URI (ảnh đã nén ở frontend)
    images: list[str] = Field(default_factory=list)  # ảnh phụ trong bộ sưu tập (product_images)


class ProductUpdateIn(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    village_code: Optional[str] = None
    price: Optional[float] = Field(default=None, gt=0)
    original_price: Optional[float] = Field(default=None, gt=0)
    stock: Optional[int] = Field(default=None, ge=0)
    description: Optional[str] = None
    material: Optional[str] = None
    size_guide: Optional[str] = None
    colors: Optional[str] = None
    sizes: Optional[str] = None
    image_url: Optional[str] = None
    images: Optional[list[str]] = None
    status: Optional[str] = None  # 'active' | 'hidden'


class ProductOut(BaseModel):
    id: int
    seller_id: int
    shop_name: str
    village_code: str
    village_name: str
    name: str
    description: Optional[str] = None
    material: Optional[str] = None
    size_guide: Optional[str] = None
    colors: list[str] = Field(default_factory=list)
    sizes: list[str] = Field(default_factory=list)
    price: float
    original_price: Optional[float] = None
    is_sale: bool = False
    is_new: bool = False
    stock: int
    sold_count: int
    rating: float
    review_count: int
    image_url: Optional[str] = None
    images: list[str] = Field(default_factory=list)
    status: str
    created_at: datetime
    updated_at: datetime


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


class SellerOrderItemOut(BaseModel):
    item_id: int
    order_id: int
    product_id: int
    product_name: str
    product_image: Optional[str] = None
    quantity: int
    color: Optional[str] = None
    size: Optional[str] = None
    price_at_purchase: float
    item_status: str
    order_status: str
    recipient_name: str
    shipping_address: str
    created_at: datetime


class SellerTransactionOut(BaseModel):
    payment_id: int
    order_id: int
    buyer_id: int
    buyer_name: str
    amount: float
    qr_image_url: Optional[str] = None
    buyer_confirmed_at: Optional[datetime] = None
    seller_confirmed_at: Optional[datetime] = None
    status: str
    created_at: datetime


# ---------- cart ----------

class CartItemIn(BaseModel):
    product_id: int
    quantity: int = Field(gt=0, default=1)
    color: Optional[str] = None
    size: Optional[str] = None


class CartItemOut(BaseModel):
    id: int
    product: ProductOut
    quantity: int
    color: Optional[str] = None
    size: Optional[str] = None
    line_total: float


class CartOut(BaseModel):
    items: list[CartItemOut]
    subtotal: float


# ---------- wishlist ----------

class WishlistIn(BaseModel):
    product_id: int


class WishlistItemOut(BaseModel):
    id: int
    product: ProductOut
    added_at: datetime


# ---------- addresses ----------

class AddressIn(BaseModel):
    label: str = Field(min_length=1, max_length=60)
    recipient_name: str = Field(min_length=1, max_length=160)
    phone: str = Field(min_length=1, max_length=30)
    address_line: str = Field(min_length=1, max_length=400)
    is_default: bool = False


class AddressOut(BaseModel):
    id: int
    label: str
    recipient_name: str
    phone: str
    address_line: str
    is_default: bool
    created_at: datetime


# ---------- orders ----------

class OrderItemIn(BaseModel):
    product_id: int
    quantity: int = Field(gt=0)
    color: Optional[str] = None
    size: Optional[str] = None


class OrderCreateIn(BaseModel):
    recipient_name: str = Field(min_length=1, max_length=160)
    recipient_email: EmailStr
    recipient_phone: Optional[str] = None
    shipping_address: str = Field(min_length=1, max_length=400)
    shipping_method: str = Field(default="standard")  # 'standard' | 'express'
    voucher_code: Optional[str] = None
    items: list[OrderItemIn] = Field(min_length=1)


class OrderItemOut(BaseModel):
    id: int
    product_id: int
    product_name: str
    product_image: Optional[str] = None
    seller_id: int
    quantity: int
    color: Optional[str] = None
    size: Optional[str] = None
    price_at_purchase: float
    item_status: str


class OrderPaymentOut(BaseModel):
    seller_id: int
    shop_name: str
    amount: float
    qr_image_url: Optional[str] = None
    buyer_confirmed_at: Optional[datetime] = None
    seller_confirmed_at: Optional[datetime] = None
    status: str


class OrderOut(BaseModel):
    id: int
    status: str
    voucher_code: Optional[str] = None
    discount_amount: float
    shipping_method: str
    shipping_fee: float
    total_price: float
    recipient_name: str
    recipient_email: str
    recipient_phone: Optional[str] = None
    shipping_address: str
    created_at: datetime
    items: list[OrderItemOut]
    payments: list[OrderPaymentOut]


class ItemStatusIn(BaseModel):
    item_status: str  # 'processing' | 'shipped' | 'delivered'


# ---------- reviews (đánh giá sao + bình luận + ảnh) ----------

class ReviewIn(BaseModel):
    rating: int = Field(ge=1, le=5)
    comment: Optional[str] = Field(default=None, max_length=2000)
    images: list[str] = Field(default_factory=list)


class ReviewOut(BaseModel):
    id: int
    product_id: int
    buyer_id: int
    buyer_name: str
    rating: int
    comment: Optional[str] = None
    images: list[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class MyReviewOut(BaseModel):
    id: int
    product_id: int
    product_name: str
    product_image: Optional[str] = None
    rating: int
    comment: Optional[str] = None
    images: list[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class ReviewListOut(BaseModel):
    average_rating: float
    review_count: int
    items: list[ReviewOut]
    my_review: Optional[ReviewOut] = None


# ---------- notifications ----------

class NotificationOut(BaseModel):
    id: int
    type: str
    title: str
    message: str
    order_id: Optional[int] = None
    is_read: bool
    created_at: datetime
