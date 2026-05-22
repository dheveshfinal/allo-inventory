from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.modules.products.service import get_all_products, get_product_by_id
from app.modules.products.schemas import ProductResponse, StockInfo
from app.modules.warehouses.schemas import WarehouseResponse

router = APIRouter(prefix="/products", tags=["products"])


def _build_product_response(product) -> ProductResponse:
    return ProductResponse(
        id=product.id,
        name=product.name,
        description=product.description,
        sku=product.sku,
        price=product.price,
        stocks=[
            StockInfo(
                warehouse=WarehouseResponse(
                    id=s.warehouse.id,
                    name=s.warehouse.name,
                    location=s.warehouse.location,
                ),
                total_units=s.total_units,
                reserved_units=s.reserved_units,
                available_units=s.available_units,
            )
            for s in product.stocks
        ],
    )


@router.get("/", response_model=list[ProductResponse])
async def list_products(db: AsyncSession = Depends(get_db)):
    """Return all products with per-warehouse stock information."""
    products = await get_all_products(db)
    return [_build_product_response(p) for p in products]


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(product_id: int, db: AsyncSession = Depends(get_db)):
    """Return a single product with stock info."""
    product = await get_product_by_id(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return _build_product_response(product)
