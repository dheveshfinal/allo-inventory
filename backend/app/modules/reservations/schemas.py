from pydantic import BaseModel
from datetime import datetime
from app.modules.reservations.models import ReservationStatus

class ReservationCreate(BaseModel):
    product_id: int
    warehouse_id: int
    quantity: int

class ReservationResponse(BaseModel):
    id: int
    stock_id: int
    quantity: int
    status: ReservationStatus
    expires_at: datetime
    created_at: datetime
    confirmed_at: datetime | None = None
    released_at: datetime | None = None

    model_config = {"from_attributes": True}

class ReservationWithDetails(ReservationResponse):
    product_name: str
    warehouse_name: str
    price: float