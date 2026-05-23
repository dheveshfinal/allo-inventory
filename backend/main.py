from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.config import settings
from app.core.redis import init_redis, close_redis
from app.core.database import engine, Base
from app.core.websocket_manager import manager
from app.modules.products.router import router as products_router
from app.modules.warehouses.router import router as warehouses_router
from app.modules.reservations.router import router as reservations_router
from app.scheduler.expiry import start_scheduler, stop_scheduler
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
logger = logging.getLogger(__name__)

# Import models after FastAPI app is created to register them with Base
def register_models():
    from app.modules.products.models import Product
    from app.modules.warehouses.models import Warehouse
    from app.modules.reservations.models import Stock, Reservation


async def auto_seed_database():
    """Automatically seed database on startup if empty."""
    from app.core.database import AsyncSessionLocal
    from app.modules.products.models import Product
    from app.modules.warehouses.models import Warehouse
    from app.modules.reservations.models import Stock
    from sqlalchemy import select

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

    STOCK_LEVELS = [
        [25, 10, 5],
        [50, 30, 20],
        [15, 8, 3],
        [40, 25, 15],
        [10, 5, 2],
        [100, 75, 60],
    ]

    async with AsyncSessionLocal() as db:
        # Check if already seeded
        result = await db.execute(select(Warehouse).limit(1))
        if result.scalar_one_or_none():
            logger.info("Database already seeded, skipping.")
            return

        logger.info("Auto-seeding database...")
        
        # Seed warehouses
        warehouses = []
        for wh_data in WAREHOUSES:
            wh = Warehouse(**wh_data)
            db.add(wh)
            warehouses.append(wh)
        await db.flush()

        # Seed products
        products = []
        for prod_data in PRODUCTS:
            p = Product(**prod_data)
            db.add(p)
            products.append(p)
        await db.flush()

        # Seed inventory
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
        logger.info(f"Database seeded: {len(warehouses)} warehouses, {len(products)} products, {len(products) * len(warehouses)} stock entries.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up...")
    # Register models
    register_models()
    # Create all tables
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created/verified.")
    except Exception as e:
        logger.error(f"Error creating tables: {e}")
    
    # Auto-seed database
    try:
        await auto_seed_database()
    except Exception as e:
        logger.error(f"Error seeding database: {e}")
    
    await init_redis()
    start_scheduler()
    logger.info("Startup complete.")
    yield
    logger.info("Shutting down...")
    stop_scheduler()
    await close_redis()
    logger.info("Shutdown complete.")


app = FastAPI(
    title="Allo Inventory API",
    description="Concurrency-safe inventory reservation system for multi-warehouse e-commerce",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(products_router, prefix="/api")
app.include_router(warehouses_router, prefix="/api")
app.include_router(reservations_router, prefix="/api")


@app.post("/api/seed")
async def seed_database():
    """Seed the database with sample data. Run once after deployment."""
    from app.core.database import AsyncSessionLocal
    from app.modules.products.models import Product
    from app.modules.warehouses.models import Warehouse
    from app.modules.reservations.models import Stock
    from sqlalchemy import select

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

    STOCK_LEVELS = [
        [25, 10, 5],
        [50, 30, 20],
        [15, 8, 3],
        [40, 25, 15],
        [10, 5, 2],
        [100, 75, 60],
    ]

    async with AsyncSessionLocal() as db:
        # Check if already seeded
        result = await db.execute(select(Warehouse).limit(1))
        if result.scalar_one_or_none():
            return {"message": "Database already seeded."}

        # Seed warehouses
        warehouses = []
        for wh_data in WAREHOUSES:
            wh = Warehouse(**wh_data)
            db.add(wh)
            warehouses.append(wh)
        await db.flush()

        # Seed products
        products = []
        for prod_data in PRODUCTS:
            p = Product(**prod_data)
            db.add(p)
            products.append(p)
        await db.flush()

        # Seed inventory
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
        return {
            "message": "Database seeded successfully",
            "warehouses": len(warehouses),
            "products": len(products),
            "stock_entries": len(products) * len(warehouses),
        }


@app.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    await manager.connect(websocket, room_id)
    try:
        while True:
            # Keep connection alive; client may send heartbeat pings
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, room_id)
        logger.info(f"WebSocket disconnected: room={room_id}")


@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "healthy", "service": "allo-inventory-api"}
