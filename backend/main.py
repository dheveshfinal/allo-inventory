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
