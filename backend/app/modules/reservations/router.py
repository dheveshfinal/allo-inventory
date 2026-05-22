from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from app.core.database import get_db
from app.core.redis import get_redis
from app.modules.reservations.service import (
    create_reservation,
    confirm_reservation,
    release_reservation,
    get_reservation_by_id,
)
from app.modules.reservations.schemas import (
    ReservationCreate,
    ReservationResponse,
    ReservationWithDetails,
)
import redis.asyncio as aioredis

router = APIRouter(prefix="/reservations", tags=["reservations"])


@router.post("/", response_model=ReservationResponse, status_code=201)
async def reserve(
    data: ReservationCreate,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
):
    """
    Create a new reservation with row-level locking.
    Returns 409 if stock is insufficient.
    Supports Idempotency-Key header to prevent duplicate reservations.
    """
    reservation = await create_reservation(db, data, redis, idempotency_key)
    return reservation


@router.get("/{reservation_id}", response_model=ReservationWithDetails)
async def get_reservation(
    reservation_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Return reservation details including product and warehouse info."""
    reservation = await get_reservation_by_id(db, reservation_id)
    if not reservation:
        raise HTTPException(status_code=404, detail="Reservation not found")
    return reservation


@router.post("/{reservation_id}/confirm", response_model=ReservationResponse)
async def confirm(
    reservation_id: int,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
):
    """
    Confirm a pending reservation (permanent stock deduction).
    Returns 410 Gone if the reservation has already expired.
    """
    return await confirm_reservation(db, reservation_id, redis, idempotency_key)


@router.post("/{reservation_id}/release", response_model=ReservationResponse)
async def release(
    reservation_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Manually release a pending reservation and return stock.
    """
    return await release_reservation(db, reservation_id)
