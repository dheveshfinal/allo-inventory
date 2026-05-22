from pydantic import BaseModel
from app.modules.warehouses.schemas import WarehouseResponse

class StockInfo(BaseModel):
    warehouse: WarehouseResponse
    total_units: int
    reserved_units: int
    available_units: int

    model_config = {"from_attributes": True}

class ProductBase(BaseModel):
    name: str
    description: str | None = None
    sku: str
    price: float

class ProductCreate(ProductBase):
    pass

class ProductResponse(ProductBase):
    id: int
    stocks: list[StockInfo] = []

    model_config = {"from_attributes": True}