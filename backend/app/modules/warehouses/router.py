from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.modules.warehouses.service import get_all_warehouses, get_warehouse_by_id
from app.modules.warehouses.schemas import WarehouseResponse

router = APIRouter(prefix="/warehouses", tags=["warehouses"])


@router.get("/", response_model=list[WarehouseResponse])
async def list_warehouses(db: AsyncSession = Depends(get_db)):
    """Return all warehouses."""
    return await get_all_warehouses(db)


@router.get("/{warehouse_id}", response_model=WarehouseResponse)
async def get_warehouse(warehouse_id: int, db: AsyncSession = Depends(get_db)):
    """Return a single warehouse by ID."""
    warehouse = await get_warehouse_by_id(db, warehouse_id)
    if not warehouse:
        raise HTTPException(status_code=404, detail="Warehouse not found")
    return warehouse
