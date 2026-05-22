from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload
from fastapi import HTTPException
from datetime import datetime, timezone
from app.modules.reservations.models import Stock, Reservation, ReservationStatus
from app.modules.products.models import Product
from app.modules.warehouses.models import Warehouse
from app.modules.reservations.schemas import ReservationCreate, ReservationWithDetails
from app.core.config import settings
from app.core.websocket_manager import manager
import redis.asyncio as aioredis
from datetime import timedelta


async def get_stock_for_update(
    db: AsyncSession,
    product_id: int,
    warehouse_id: int
) -> Stock:
    # SELECT FOR UPDATE — locks the row so no other transaction can modify it
    result = await db.execute(
        select(Stock)
        .where(
            Stock.product_id == product_id,
            Stock.warehouse_id == warehouse_id
        )
        .with_for_update()  # this is the key line — row level lock
    )
    stock = result.scalar_one_or_none()
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found for this product/warehouse")
    return stock


async def create_reservation(
    db: AsyncSession,
    data: ReservationCreate,
    redis: aioredis.Redis,
    idempotency_key: str | None = None
) -> Reservation:

    # check idempotency key first
    if idempotency_key:
        cached = await redis.get(f"idempotency:{idempotency_key}")
        if cached:
            # return existing reservation
            reservation_id = int(cached)
            result = await db.execute(
                select(Reservation).where(Reservation.id == reservation_id)
            )
            return result.scalar_one_or_none()

    async with db.begin():
        # lock the stock row
        stock = await get_stock_for_update(db, data.product_id, data.warehouse_id)

        available = stock.total_units - stock.reserved_units

        if available < data.quantity:
            raise HTTPException(
                status_code=409,
                detail=f"Not enough stock. Available: {available}, Requested: {data.quantity}"
            )

        # decrement available by incrementing reserved
        stock.reserved_units += data.quantity

        # create reservation
        expires_at = datetime.now(timezone.utc) + timedelta(
            minutes=settings.RESERVATION_EXPIRY_MINUTES
        )

        reservation = Reservation(
            stock_id=stock.id,
            quantity=data.quantity,
            status=ReservationStatus.pending,
            expires_at=expires_at,
            idempotency_key=idempotency_key
        )

        db.add(reservation)
        await db.flush()  # get the reservation id before commit
        await db.refresh(reservation)

    # store idempotency key in redis for 24 hours
    if idempotency_key:
        await redis.setex(
            f"idempotency:{idempotency_key}",
            86400,  # 24 hours
            str(reservation.id)
        )

    # broadcast stock update to all connected clients
    await manager.broadcast_to_all({
        "type": "stock_update",
        "product_id": data.product_id,
        "warehouse_id": data.warehouse_id,
        "available": stock.total_units - stock.reserved_units
    })

    return reservation


async def confirm_reservation(
    db: AsyncSession,
    reservation_id: int,
    redis: aioredis.Redis,
    idempotency_key: str | None = None
) -> Reservation:

    # check idempotency
    if idempotency_key:
        cached = await redis.get(f"idempotency:confirm:{idempotency_key}")
        if cached:
            result = await db.execute(
                select(Reservation).where(Reservation.id == reservation_id)
            )
            return result.scalar_one_or_none()

    async with db.begin():
        result = await db.execute(
            select(Reservation)
            .where(Reservation.id == reservation_id)
            .with_for_update()
        )
        reservation = result.scalar_one_or_none()

        if not reservation:
            raise HTTPException(status_code=404, detail="Reservation not found")

        if reservation.status != ReservationStatus.pending:
            raise HTTPException(
                status_code=400,
                detail=f"Reservation is already {reservation.status}"
            )

        # check if expired
        now = datetime.now(timezone.utc)
        if reservation.expires_at.replace(tzinfo=timezone.utc) < now:
            # auto release
            stock_result = await db.execute(
                select(Stock).where(Stock.id == reservation.stock_id).with_for_update()
            )
            stock = stock_result.scalar_one()
            stock.reserved_units -= reservation.quantity
            reservation.status = ReservationStatus.released
            reservation.released_at = now
            raise HTTPException(status_code=410, detail="Reservation has expired")

        reservation.status = ReservationStatus.confirmed
        reservation.confirmed_at = now

    if idempotency_key:
        await redis.setex(
            f"idempotency:confirm:{idempotency_key}",
            86400,
            str(reservation_id)
        )

    # broadcast reservation confirmed
    await manager.broadcast_to_all({
        "type": "reservation_confirmed",
        "reservation_id": reservation_id
    })

    return reservation


async def release_reservation(
    db: AsyncSession,
    reservation_id: int
) -> Reservation:

    async with db.begin():
        result = await db.execute(
            select(Reservation)
            .where(Reservation.id == reservation_id)
            .with_for_update()
        )
        reservation = result.scalar_one_or_none()

        if not reservation:
            raise HTTPException(status_code=404, detail="Reservation not found")

        if reservation.status != ReservationStatus.pending:
            raise HTTPException(
                status_code=400,
                detail=f"Reservation is already {reservation.status}"
            )

        # give stock back
        stock_result = await db.execute(
            select(Stock)
            .where(Stock.id == reservation.stock_id)
            .with_for_update()
        )
        stock = stock_result.scalar_one()
        stock.reserved_units -= reservation.quantity

        reservation.status = ReservationStatus.released
        reservation.released_at = datetime.now(timezone.utc)

    # broadcast stock update
    await manager.broadcast_to_all({
        "type": "stock_update",
        "stock_id": reservation.stock_id,
        "available": stock.total_units - stock.reserved_units
    })

    return reservation


async def release_expired_reservations(db: AsyncSession):
    """Called by scheduler every 2 minutes"""
    now = datetime.now(timezone.utc)

    async with db.begin():
        # find all expired pending reservations
        result = await db.execute(
            select(Reservation)
            .where(
                Reservation.status == ReservationStatus.pending,
                Reservation.expires_at < now
            )
            .with_for_update()
        )
        expired = result.scalars().all()

        for reservation in expired:
            stock_result = await db.execute(
                select(Stock)
                .where(Stock.id == reservation.stock_id)
                .with_for_update()
            )
            stock = stock_result.scalar_one()
            stock.reserved_units -= reservation.quantity
            reservation.status = ReservationStatus.released
            reservation.released_at = now

            # broadcast stock update
            await manager.broadcast_to_all({
                "type": "stock_update",
                "stock_id": reservation.stock_id,
                "available": stock.total_units - stock.reserved_units
            })

    return len(expired)


async def get_reservation_by_id(
    db: AsyncSession,
    reservation_id: int
) -> ReservationWithDetails | None:
    result = await db.execute(
        select(Reservation)
        .where(Reservation.id == reservation_id)
        .options(
            selectinload(Reservation.stock).selectinload(Stock.product),
            selectinload(Reservation.stock).selectinload(Stock.warehouse)
        )
    )
    reservation = result.scalar_one_or_none()

    if not reservation:
        return None

    return ReservationWithDetails(
        id=reservation.id,
        stock_id=reservation.stock_id,
        quantity=reservation.quantity,
        status=reservation.status,
        expires_at=reservation.expires_at,
        created_at=reservation.created_at,
        confirmed_at=reservation.confirmed_at,
        released_at=reservation.released_at,
        product_name=reservation.stock.product.name,
        warehouse_name=reservation.stock.warehouse.name,
        price=reservation.stock.product.price
    )