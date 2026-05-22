from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.modules.products.models import Product
from app.modules.reservations.models import Stock

async def get_all_products(db: AsyncSession) -> list[Product]:
    result = await db.execute(
        select(Product).options(
            selectinload(Product.stocks).selectinload(Stock.warehouse)
        )
    )
    return result.scalars().all()

async def get_product_by_id(db: AsyncSession, product_id: int) -> Product | None:
    result = await db.execute(
        select(Product)
        .where(Product.id == product_id)
        .options(
            selectinload(Product.stocks).selectinload(Stock.warehouse)
        )
    )
    return result.scalar_one_or_none()