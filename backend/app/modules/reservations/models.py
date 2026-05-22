from sqlalchemy import String, Integer, ForeignKey, DateTime, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum

class ReservationStatus(str, enum.Enum):
    pending = "pending"
    confirmed = "confirmed"
    released = "released"

class Stock(Base):
    __tablename__ = "stocks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    warehouse_id: Mapped[int] = mapped_column(ForeignKey("warehouses.id"), nullable=False)
    total_units: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    reserved_units: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # available = total_units - reserved_units (computed in queries)

    # relationships
    product: Mapped["Product"] = relationship("Product", back_populates="stocks")
    warehouse: Mapped["Warehouse"] = relationship("Warehouse", back_populates="stocks")
    reservations: Mapped[list["Reservation"]] = relationship("Reservation", back_populates="stock")

    @property
    def available_units(self) -> int:
        return self.total_units - self.reserved_units


class Reservation(Base):
    __tablename__ = "reservations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    stock_id: Mapped[int] = mapped_column(ForeignKey("stocks.id"), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[ReservationStatus] = mapped_column(
        Enum(ReservationStatus),
        nullable=False,
        default=ReservationStatus.pending
    )
    idempotency_key: Mapped[str] = mapped_column(String(255), nullable=True, unique=True)
    expires_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    confirmed_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=True)
    released_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=True)

    # relationships
    stock: Mapped["Stock"] = relationship("Stock", back_populates="reservations")