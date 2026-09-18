"""Chuyển dict -> Pydantic schema. Tách riêng để router nào cũng lắp ráp
UserOut/ProductOut giống hệt nhau, không lặp code."""

import psycopg

from app.schemas import ProductOut, SellerProfileOut, UserOut

PRODUCT_SELECT = """
SELECT
    p.id, p.seller_id, p.name, p.description, p.material, p.size_guide,
    p.colors, p.sizes, p.price, p.original_price, p.stock, p.sold_count,
    p.rating, p.review_count, p.image_url, p.status, p.created_at, p.updated_at,
    (p.original_price IS NOT NULL AND p.original_price > p.price) AS is_sale_flag,
    (p.created_at > NOW() - INTERVAL '14 days') AS is_new_flag,
    COALESCE(
        (SELECT array_agg(pi.image_url ORDER BY pi.sort_order, pi.id)
         FROM product_images pi WHERE pi.product_id = p.id),
        ARRAY[]::text[]
    ) AS images,
    v.code AS village_code, v.name AS village_name,
    COALESCE(sp.shop_name, u.name) AS shop_name
FROM products p
JOIN villages v ON v.id = p.village_id
JOIN users u ON u.id = p.seller_id
LEFT JOIN seller_profiles sp ON sp.user_id = p.seller_id
"""


def _split_csv(value: str | None) -> list[str]:
    if not value:
        return []
    return [part.strip() for part in value.split(",") if part.strip()]


def row_to_product(row: dict) -> ProductOut:
    return ProductOut(
        id=row["id"],
        seller_id=row["seller_id"],
        shop_name=row["shop_name"],
        village_code=row["village_code"],
        village_name=row["village_name"],
        name=row["name"],
        description=row["description"],
        material=row["material"],
        size_guide=row["size_guide"],
        colors=_split_csv(row["colors"]),
        sizes=_split_csv(row["sizes"]),
        price=row["price"],
        original_price=row["original_price"],
        is_sale=bool(row["is_sale_flag"]),
        is_new=bool(row["is_new_flag"]),
        stock=row["stock"],
        sold_count=row["sold_count"],
        rating=row["rating"],
        review_count=row["review_count"],
        image_url=row["image_url"],
        images=list(row["images"] or []),
        status=row["status"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def row_to_user(db: psycopg.Connection, user: dict) -> UserOut:
    seller = None
    if user["is_seller"]:
        sp = db.execute(
            """SELECT sp.shop_name, sp.phone, sp.bio, sp.payment_qr_url,
                      v.code AS village_code, v.name AS village_name
               FROM seller_profiles sp JOIN villages v ON v.id = sp.village_id
               WHERE sp.user_id = %s""",
            (user["id"],),
        ).fetchone()
        if sp is not None:
            seller = SellerProfileOut(
                shop_name=sp["shop_name"],
                village_code=sp["village_code"],
                village_name=sp["village_name"],
                phone=sp["phone"],
                bio=sp["bio"],
                payment_qr_url=sp["payment_qr_url"],
            )
    return UserOut(
        id=user["id"],
        name=user["name"],
        username=user["username"],
        email=user["email"],
        phone=user["phone"],
        avatar_url=user["avatar_url"],
        is_seller=bool(user["is_seller"]),
        created_at=user["created_at"],
        seller=seller,
    )
