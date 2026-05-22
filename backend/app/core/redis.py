import ssl
import redis.asyncio as aioredis
from app.core.config import settings

redis_client: aioredis.Redis = None

async def get_redis() -> aioredis.Redis:
    return redis_client

async def init_redis():
    global redis_client
    
    redis_url = settings.REDIS_URL
    
    if not redis_url:
        raise RuntimeError("REDIS_URL is not set in environment variables")
    
    # Use SSL for Upstash (rediss://) — skip cert verification
    ssl_context = None
    if redis_url.startswith("rediss://"):
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
    
    redis_client = aioredis.from_url(
        redis_url,
        encoding="utf-8",
        decode_responses=True,
        ssl=ssl_context
    )

async def close_redis():
    global redis_client
    if redis_client:
        await redis_client.aclose()  # fixed: close() is deprecated, use aclose()