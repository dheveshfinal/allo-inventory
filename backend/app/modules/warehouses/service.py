from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.modules.warehouses.models import Warehouse

async def get_all_warehouses(db: AsyncSession) -> list[Warehouse]:
    result = await db.execute(select(Warehouse))
    return result.scalars().all()

async def get_warehouse_by_id(db: AsyncSession, warehouse_id: int) -> Warehouse | None:
    result = await db.execute(
        select(Warehouse).where(Warehouse.id == warehouse_id)
    )
    return result.scalar_one_or_none()