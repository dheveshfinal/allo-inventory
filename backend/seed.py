"""
Seed script — run once to populate the database with sample data.
Usage: python seed.py
"""
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from app.modules.products.models import Product
from app.modules.warehouses.models import Warehouse
from app.modules.reservations.models import Stock


WAREHOUSES = [
    {"name": "North Hub", "location": "New York, NY"},
    {"name": "South Hub", "location": "Dallas, TX"},
    {"name": "West Hub", "location": "Los Angeles, CA"},
]

PRODUCTS = [
    {"name": "Wireless Noise-Cancelling Headphones", "description": "Premium over-ear headphones with ANC, 30hr battery.", "sku": "WH-ANC-001", "price": 299.99},
    {"name": "Mechanical Keyboard TKL", "description": "Tenkeyless RGB mechanical keyboard with Cherry MX switches.", "sku": "KB-MX-TKL", "price": 149.99},
    {"name": "4K USB-C Monitor 27\"", "description": "Ultra-sharp 4K IPS display with USB-C PD charging.", "sku": "MON-4K-27", "price": 549.99},
    {"name": "Ergonomic Mesh Chair", "description": "Lumbar support mesh office chair with adjustable arms.", "sku": "CHR-ERGO-1", "price": 399.00},
    {"name": "Smart Standing Desk", "description": "Electric height-adjustable desk, dual-motor, memory presets.", "sku": "DSK-ELEC-1", "price": 799.00},
    {"name": "Portable SSD 1TB", "description": "Ultra-fast USB 3.2 Gen 2 portable solid-state drive.", "sku": "SSD-1TB-USB", "price": 89.99},
]

# Stock levels: [north, south, west] units per product
STOCK_LEVELS = [
    [25, 10, 5],   # Headphones — low west stock to show scarcity
    [50, 30, 20],
    [15, 8, 3],    # Monitor — scarce
    [40, 25, 15],
    [10, 5, 2],    # Standing desk — very scarce
    [100, 75, 60],
]


async def seed(db: AsyncSession):
    # Check if already seeded
    from sqlalchemy import select
    result = await db.execute(select(Warehouse).limit(1))
    if result.scalar_one_or_none():
        print("Database already seeded. Skipping.")
        return

    print("Seeding warehouses...")
    warehouses = []
    for wh_data in WAREHOUSES:
        wh = Warehouse(**wh_data)
        db.add(wh)
        warehouses.append(wh)
    await db.flush()

    print("Seeding products...")
    products = []
    for prod_data in PRODUCTS:
        p = Product(**prod_data)
        db.add(p)
        products.append(p)
    await db.flush()

    print("Seeding inventory (stock)...")
    for i, product in enumerate(products):
        for j, warehouse in enumerate(warehouses):
            stock = Stock(
                product_id=product.id,
                warehouse_id=warehouse.id,
                total_units=STOCK_LEVELS[i][j],
                reserved_units=0,
            )
            db.add(stock)

    await db.commit()
    print(f"Successfully seeded {len(warehouses)} warehouses, {len(products)} products, {len(products) * len(warehouses)} stock entries.")


async def main():
    async with AsyncSessionLocal() as db:
        await seed(db)


if __name__ == "__main__":
    asyncio.run(main())
