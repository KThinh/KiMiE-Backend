"""Chuyển sqlite3.Row -> Pydantic schema. Tách riêng để router nào cũng lắp ráp
UserOut/ProductOut giống hệt nhau, không lặp code."""

import sqlite3

from app.schemas import ProductOut, SellerProfileOut, UserOut

PRODUCT_SELECT = """
SELECT
    p.id, p.seller_id, p.name, p.description, p.price, p.stock, p.sold_count,
    p.rating, p.review_count, p.image_url, p.status, p.created_at, p.updated_at,
    v.code AS village_code, v.name AS village_name,
    COALESCE(sp.shop_name, u.name) AS shop_name
FROM products p
JOIN villages v ON v.id = p.village_id
JOIN users u ON u.id = p.seller_id
LEFT JOIN seller_profiles sp ON sp.user_id = p.seller_id
"""


def row_to_product(row: sqlite3.Row) -> ProductOut:
    return ProductOut(
        id=row["id"],
        seller_id=row["seller_id"],
        shop_name=row["shop_name"],
        village_code=row["village_code"],
        village_name=row["village_name"],
        name=row["name"],
        description=row["description"],
        price=row["price"],
        stock=row["stock"],
        sold_count=row["sold_count"],
        rating=row["rating"],
        review_count=row["review_count"],
        image_url=row["image_url"],
        status=row["status"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def row_to_user(db: sqlite3.Connection, user: sqlite3.Row) -> UserOut:
    seller = None
    if user["is_seller"]:
        sp = db.execute(
            """SELECT sp.shop_name, sp.phone, sp.bio, v.code AS village_code, v.name AS village_name
               FROM seller_profiles sp JOIN villages v ON v.id = sp.village_id
               WHERE sp.user_id = ?""",
            (user["id"],),
        ).fetchone()
        if sp is not None:
            seller = SellerProfileOut(
                shop_name=sp["shop_name"],
                village_code=sp["village_code"],
                village_name=sp["village_name"],
                phone=sp["phone"],
                bio=sp["bio"],
            )
    return UserOut(
        id=user["id"],
        name=user["name"],
        email=user["email"],
        phone=user["phone"],
        is_seller=bool(user["is_seller"]),
        created_at=user["created_at"],
        seller=seller,
    )
