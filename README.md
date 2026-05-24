# 🏭 Allo Inventory Live(https://allo-inventory-roan.vercel.app/)

> **Concurrency-safe inventory reservation system for multi-warehouse e-commerce**

A full-stack application that solves the classic "oversell" problem — ensuring that multiple concurrent users can never reserve more stock than physically exists. Built with **PostgreSQL row-level locking**, **Redis idempotency**, **WebSocket real-time updates**, and a **background expiry scheduler**.

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Tech Stack](#-tech-stack)
- [Architecture](#-architecture)
- [Project Structure](#-project-structure)
- [Core Features](#-core-features)
- [Data Models](#-data-models)
- [API Reference](#-api-reference)
- [Reservation Lifecycle](#-reservation-lifecycle)
- [Real-Time Updates (WebSocket)](#-real-time-updates-websocket)
- [Background Scheduler](#-background-scheduler)
- [Local Development Setup](#-local-development-setup)
- [Docker Setup](#-docker-setup)
- [Environment Variables](#-environment-variables)
- [Database Seeding](#-database-seeding)
- [Deployment](#-deployment)

---

## 🔍 Overview

Allo Inventory manages stock across multiple warehouses and provides a **two-phase reservation workflow**:

1. **Reserve** — Temporarily hold stock for a customer (row-level lock prevents oversell)
2. **Confirm** — Permanently deduct stock when payment succeeds
3. **Release** — Return stock if the customer cancels or the reservation expires

All stock operations are **atomic** via PostgreSQL `SELECT FOR UPDATE`, and every mutating API supports an **`Idempotency-Key`** header backed by Redis to guarantee exactly-once semantics even under network retries.

---

## 🛠 Tech Stack

### Backend

| Layer | Technology | Version |
|---|---|---|
| Framework | **FastAPI** | 0.111.0 |
| ASGI Server | **Uvicorn** | 0.29.0 |
| ORM | **SQLAlchemy** (async) | 2.0.30 |
| Async DB Driver | **asyncpg** | 0.29.0 |
| Sync DB Driver | **psycopg2-binary** | 2.9.9 |
| Migrations | **Alembic** | 1.13.1 |
| Database | **PostgreSQL** | 15 |
| Cache / Idempotency | **Redis** | 7 (client: redis-py 5.0.4) |
| Scheduler | **APScheduler** | 3.10.4 |
| Validation | **Pydantic v2** | 2.7.1 |
| Settings | **pydantic-settings** | 2.2.1 |
| WebSockets | **websockets** | 12.0 |
| Env | **python-dotenv** | 1.0.1 |
| Language | **Python** | 3.11+ |

### Frontend

| Layer | Technology | Version |
|---|---|---|
| Framework | **React** | 18.2 |
| Language | **TypeScript** | 5.2 |
| Build Tool | **Vite** | 5.2 |
| Routing | **React Router DOM** | 6.22 |
| Styling | **Tailwind CSS** | 4.x |
| Icons | **Lucide React** | 1.16 |
| Utilities | **clsx**, **tailwind-merge** | latest |

### Infrastructure

| Component | Technology |
|---|---|
| Containerization | **Docker** + **Docker Compose** |
| Frontend Deployment | **Vercel** |
| Backend Deployment | **Docker** (self-hosted / cloud) |

---

## 🏗 Architecture

```
┌───────────────────────────────────────────────────────────────┐
│                         Browser / Client                       │
│              React + TypeScript + Tailwind CSS                 │
│         (Products Page · Warehouses Page · Checkout Page)      │
└───────────────┬───────────────────────────┬───────────────────┘
                │  REST API (HTTP/HTTPS)     │  WebSocket (ws://)
                ▼                           ▼
┌───────────────────────────────────────────────────────────────┐
│                       FastAPI Backend                          │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────┐  │
│  │  /products   │  │ /warehouses  │  │   /reservations    │  │
│  │   router     │  │   router     │  │      router        │  │
│  └──────┬───────┘  └──────┬───────┘  └─────────┬──────────┘  │
│         │                 │                    │              │
│         └────────────┬────┘────────────────────┘              │
│                      │                                        │
│              ┌───────▼───────┐   ┌─────────────────────┐     │
│              │  SQLAlchemy   │   │  WebSocket Manager   │     │
│              │  Async ORM    │   │  (broadcast_to_all)  │     │
│              └───────┬───────┘   └─────────────────────┘     │
│                      │                                        │
│         ┌────────────┼────────────┐                          │
│         ▼            ▼            ▼                          │
│  ┌─────────────┐ ┌────────┐ ┌──────────────┐                 │
│  │  PostgreSQL │ │ Redis  │ │  APScheduler │                 │
│  │     :5433   │ │ :6379  │ │ (every 2min) │                 │
│  │ SELECT FOR  │ │ Idem-  │ │ Expiry Job   │                 │
│  │   UPDATE    │ │ potency│ │              │                 │
│  └─────────────┘ └────────┘ └──────────────┘                 │
└───────────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
allo-inventory/
├── docker-compose.yml          # Orchestrates all 4 services
├── SEED_DATABASE.txt           # Manual seed instructions
│
├── backend/
│   ├── main.py                 # FastAPI app, middleware, lifespan, WebSocket endpoint
│   ├── requirements.txt        # Python dependencies
│   ├── Dockerfile              # Backend container image
│   ├── alembic.ini             # Alembic migration config
│   ├── seed.py                 # Manual DB seed script
│   ├── .env                    # Local environment variables
│   │
│   ├── alembic/                # Migration history
│   │
│   └── app/
│       ├── core/
│       │   ├── config.py           # Pydantic settings (env vars)
│       │   ├── database.py         # Async engine + session factory
│       │   ├── redis.py            # Redis client init/close
│       │   └── websocket_manager.py # Room-based WebSocket broadcaster
│       │
│       ├── modules/
│       │   ├── products/
│       │   │   ├── models.py       # Product SQLAlchemy model
│       │   │   ├── schemas.py      # Pydantic request/response schemas
│       │   │   ├── service.py      # Business logic
│       │   │   └── router.py       # GET /api/products
│       │   │
│       │   ├── warehouses/
│       │   │   ├── models.py       # Warehouse SQLAlchemy model
│       │   │   ├── schemas.py      # Pydantic schemas
│       │   │   ├── service.py      # Business logic
│       │   │   └── router.py       # GET /api/warehouses
│       │   │
│       │   └── reservations/
│       │       ├── models.py       # Stock + Reservation models + ReservationStatus enum
│       │       ├── schemas.py      # Pydantic schemas
│       │       ├── service.py      # Core reservation logic (lock · reserve · confirm · release)
│       │       └── router.py       # POST/GET /api/reservations
│       │
│       └── scheduler/
│           └── expiry.py           # APScheduler job — releases expired reservations every 2min
│
└── frontend/
    ├── package.json            # npm dependencies + scripts
    ├── vite.config.ts          # Vite bundler config
    ├── tsconfig.json           # TypeScript config
    ├── vercel.json             # Vercel SPA rewrite rules
    ├── Dockerfile              # Frontend container image
    ├── .env.local              # Local environment variables
    │
    └── src/
        ├── App.tsx             # Root component + React Router routes
        ├── main.tsx            # React DOM entry point
        ├── index.css           # Global Tailwind CSS
        │
        ├── lib/                # Shared utilities / API base client
        │
        └── modules/
            ├── products/
            │   ├── ProductsPage.tsx      # Product listing with stock per warehouse
            │   ├── productService.ts     # API calls to /api/products
            │   ├── useProducts.ts        # React hook (fetch + WebSocket listener)
            │   └── types.ts              # TypeScript interfaces
            │
            ├── warehouses/
            │   └── WarehousesPage.tsx    # Warehouse listing
            │
            └── reservations/
                ├── ReservationPage.tsx   # Checkout / reservation details page
                ├── reservationService.ts # API calls to /api/reservations
                ├── useReservation.ts     # React hook
                └── types.ts             # TypeScript interfaces
```

---

## ✨ Core Features

### 1. Concurrency-Safe Reservations
Every stock mutation uses **PostgreSQL `SELECT FOR UPDATE`** row-level locking. This means two simultaneous requests for the last unit will serialize — one succeeds, the other gets a `409 Conflict` — never an oversell.

### 2. Two-Phase Reservation Lifecycle
```
PENDING ──► CONFIRMED  (payment succeeded)
   │
   └──────► RELEASED   (cancelled or expired)
```

### 3. Idempotency via Redis
Every `POST /reservations` and `POST /reservations/{id}/confirm` call accepts an **`Idempotency-Key`** HTTP header. The key is cached in Redis for **24 hours**. Retrying with the same key returns the original response without creating a duplicate reservation.

### 4. Auto-Expiry Scheduler
Reservations expire after **10 minutes** (configurable). **APScheduler** runs a cleanup job **every 2 minutes** that:
- Finds all `PENDING` reservations past their `expires_at`
- Releases them back to available stock
- Broadcasts a `stock_update` WebSocket event

### 5. Real-Time WebSocket Updates
Any stock change (reserve, confirm, release, auto-expire) is **broadcast to all connected clients** via WebSocket at `ws://<host>/ws/{room_id}`. The frontend listens and updates stock numbers live without polling.

### 6. Multi-Warehouse Inventory
Products exist across **multiple warehouses**, each with independent `total_units` and `reserved_units`. The dashboard shows per-warehouse availability for every product.

### 7. Auto Database Seeding
On first startup the backend automatically seeds:
- **3 Warehouses** (North Hub / South Hub / West Hub)
- **6 Products** (headphones, keyboard, monitor, chair, desk, SSD)
- **18 Stock entries** (every product × every warehouse)

---

## 🗃 Data Models

### `products`
| Column | Type | Notes |
|---|---|---|
| `id` | Integer PK | Auto-increment |
| `name` | String | Product name |
| `description` | String | Description |
| `sku` | String | Unique SKU |
| `price` | Float | Unit price |

### `warehouses`
| Column | Type | Notes |
|---|---|---|
| `id` | Integer PK | Auto-increment |
| `name` | String | Warehouse name |
| `location` | String | City, State |

### `stocks`
| Column | Type | Notes |
|---|---|---|
| `id` | Integer PK | Auto-increment |
| `product_id` | FK → products | |
| `warehouse_id` | FK → warehouses | |
| `total_units` | Integer | Physical stock |
| `reserved_units` | Integer | Currently held |
| *(computed)* | `available_units` | `total - reserved` |

### `reservations`
| Column | Type | Notes |
|---|---|---|
| `id` | Integer PK | Auto-increment |
| `stock_id` | FK → stocks | |
| `quantity` | Integer | Units reserved |
| `status` | Enum | `pending` / `confirmed` / `released` |
| `idempotency_key` | String (unique) | Dedup key |
| `expires_at` | DateTime (TZ) | TTL for pending hold |
| `created_at` | DateTime (TZ) | Auto server time |
| `confirmed_at` | DateTime (TZ) | Set on confirm |
| `released_at` | DateTime (TZ) | Set on release/expire |

---

## 📡 API Reference

Base URL: `http://localhost:8000`

### Health
| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Health check → `{"status":"healthy"}` |

### Products
| Method | Path | Description |
|---|---|---|
| `GET` | `/api/products` | List all products with per-warehouse stock |
| `GET` | `/api/products/{id}` | Get a single product with stock info |

### Warehouses
| Method | Path | Description |
|---|---|---|
| `GET` | `/api/warehouses` | List all warehouses |
| `GET` | `/api/warehouses/{id}` | Get a single warehouse |

### Reservations
| Method | Path | Description |
|---|---|---|
| `POST` | `/api/reservations` | Create a reservation (row-level lock) |
| `GET` | `/api/reservations/{id}` | Get reservation details |
| `POST` | `/api/reservations/{id}/confirm` | Confirm a pending reservation |
| `POST` | `/api/reservations/{id}/release` | Manually release a reservation |

### Seed
| Method | Path | Description |
|---|---|---|
| `POST` | `/api/seed` | Seed the database (idempotent) |

### WebSocket
| Method | Path | Description |
|---|---|---|
| `WS` | `/ws/{room_id}` | Real-time stock update stream |

> **Interactive API Docs**: `http://localhost:8000/docs` (Swagger UI)

#### Example — Create Reservation

```http
POST /api/reservations
Content-Type: application/json
Idempotency-Key: order-abc-123

{
  "product_id": 1,
  "warehouse_id": 2,
  "quantity": 3
}
```

**Response `201`**
```json
{
  "id": 42,
  "stock_id": 5,
  "quantity": 3,
  "status": "pending",
  "expires_at": "2026-05-23T10:10:00Z",
  "created_at": "2026-05-23T10:00:00Z"
}
```

**Response `409`** — Insufficient stock
```json
{ "detail": "Not enough stock. Available: 1, Requested: 3" }
```

---

## 🔄 Reservation Lifecycle

```
Client                          Backend                        Database / Redis
  │                               │                                  │
  │── POST /api/reservations ─────►│                                  │
  │   Idempotency-Key: xyz         │── Check Redis key "xyz" ────────►│
  │                               │◄─ (miss)                         │
  │                               │── BEGIN TRANSACTION              │
  │                               │── SELECT * FROM stocks           │
  │                               │   WHERE ... FOR UPDATE ─────────►│ ← row lock
  │                               │◄─ stock row (locked)             │
  │                               │── Check available >= quantity    │
  │                               │── UPDATE reserved_units += qty   │
  │                               │── INSERT INTO reservations       │
  │                               │── COMMIT ────────────────────────►│
  │                               │── Redis SET "xyz" = res.id ─────►│
  │                               │── WS broadcast stock_update      │
  │◄─ 201 {reservation} ──────────│                                  │
  │                               │                                  │
  │── POST /reservations/42/confirm►│                                  │
  │                               │── SELECT FOR UPDATE (reservation)│
  │                               │── Check not expired              │
  │                               │── SET status = "confirmed"       │
  │                               │── COMMIT                         │
  │                               │── WS broadcast confirmed         │
  │◄─ 200 {reservation} ──────────│                                  │
  │                               │                                  │
  │   [or 10 min pass]            │                                  │
  │                               │── APScheduler fires (every 2min) │
  │                               │── Find expired PENDING rows      │
  │                               │── SET status = "released"        │
  │                               │── reserved_units -= qty          │
  │                               │── WS broadcast stock_update      │
```

---

## 🔌 Real-Time Updates (WebSocket)

Connect to `ws://localhost:8000/ws/{room_id}` (any string as `room_id`).

### Event: `stock_update`
Fired when stock availability changes (reserve / release / expire).
```json
{
  "type": "stock_update",
  "product_id": 1,
  "warehouse_id": 2,
  "available": 22
}
```

### Event: `reservation_confirmed`
Fired when a reservation moves to `confirmed`.
```json
{
  "type": "reservation_confirmed",
  "reservation_id": 42
}
```

The frontend uses this to **live-refresh** displayed stock counts without any polling.

---

## ⏱ Background Scheduler

**APScheduler** (`AsyncIOScheduler`) starts on app startup and runs a single recurring job:

| Job ID | Interval | Function |
|---|---|---|
| `expiry_cleanup` | Every **2 minutes** | `release_expired_reservations()` |

The job:
1. Queries all `PENDING` reservations where `expires_at < NOW()`
2. Uses `SELECT FOR UPDATE` on each stock row to safely decrement `reserved_units`
3. Marks each reservation as `released`
4. Broadcasts a `stock_update` WebSocket event per released reservation
5. Logs the count of released reservations

Default TTL is **10 minutes** (`RESERVATION_EXPIRY_MINUTES=10` in `.env`).

---

## 🚀 Local Development Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker Desktop (for PostgreSQL + Redis)
- Git

### 1. Start Infrastructure (PostgreSQL + Redis)

```bash
docker compose up postgres redis -d
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Copy and edit environment variables
copy .env.example .env       # Windows
# cp .env.example .env       # macOS/Linux

# Run database migrations
alembic upgrade head

# Start the backend server
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Backend runs at: **http://localhost:8000**
Swagger UI: **http://localhost:8000/docs**

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Copy and edit environment variables
copy .env.local.example .env.local   # Windows

# Start the dev server
npm run dev
```

Frontend runs at: **http://localhost:5173**

---

## 🐳 Docker Setup

The full stack (PostgreSQL + Redis + Backend + Frontend) can be started with a single command:

```bash
docker compose up --build
```

| Service | Container | Port |
|---|---|---|
| PostgreSQL | `allo_postgres` | `5433:5432` |
| Redis | `allo_redis` | `6379:6379` |
| FastAPI Backend | `allo_backend` | `8000:8000` |
| React Frontend | `allo_frontend` | `5173:5173` |

On first boot, Docker Compose automatically:
1. Runs `alembic upgrade head` to apply migrations
2. Runs `seed.py` to populate sample data
3. Starts Uvicorn with `--reload`

To stop and remove containers:
```bash
docker compose down
```

To reset the database volume:
```bash
docker compose down -v
```

---

## ⚙ Environment Variables

### Backend (`backend/.env`)

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://postgres:postgres@localhost:5433/allo` | Async DB URL (asyncpg) |
| `SYNC_DATABASE_URL` | `postgresql://postgres:postgres@localhost:5433/allo` | Sync DB URL (Alembic) |
| `REDIS_URL` | `redis://localhost:6379` | Redis connection URL |
| `FRONTEND_URL` | `http://localhost:3000` | Allowed CORS origin |
| `RESERVATION_EXPIRY_MINUTES` | `10` | Reservation TTL in minutes |

### Frontend (`frontend/.env.local`)

| Variable | Description |
|---|---|
| `VITE_API_URL` | Backend base URL (e.g. `http://localhost:8000`) |
| `VITE_WS_URL` | WebSocket base URL (e.g. `ws://localhost:8000`) |

---

## 🌱 Database Seeding

Seeding happens automatically on backend startup if the database is empty. To seed manually:

**Via API:**
```bash
curl -X POST http://localhost:8000/api/seed
```

**Via Python script:**
```bash
cd backend
python seed.py
```

Sample data includes:

**Warehouses:**
- North Hub — New York, NY
- South Hub — Dallas, TX
- West Hub — Los Angeles, CA

**Products:**
- Wireless Noise-Cancelling Headphones (SKU: `WH-ANC-001`) — $299.99
- Mechanical Keyboard TKL (SKU: `KB-MX-TKL`) — $149.99
- 4K USB-C Monitor 27" (SKU: `MON-4K-27`) — $549.99
- Ergonomic Mesh Chair (SKU: `CHR-ERGO-1`) — $399.00
- Smart Standing Desk (SKU: `DSK-ELEC-1`) — $799.00
- Portable SSD 1TB (SKU: `SSD-1TB-USB`) — $89.99

---

## ☁ Deployment

### Frontend — Vercel

The frontend is configured for Vercel SPA deployment. The `vercel.json` rewrites all routes to `index.html` for client-side routing:

```json
{
  "rewrites": [{ "source": "/(.*)", "destination": "/index.html" }]
}
```

Deploy:
```bash
cd frontend
npx vercel --prod
```

Set `VITE_API_URL` and `VITE_WS_URL` in your Vercel project environment variables.

### Backend — Docker

The backend Dockerfile builds a production-ready image:

```bash
docker build -t allo-backend ./backend
docker run -p 8000:8000 --env-file ./backend/.env allo-backend
```

Or use the full Docker Compose setup on any cloud VM (AWS EC2, DigitalOcean Droplet, Railway, Render, etc.).

---

## 📄 License

MIT — use freely, contribute back.
