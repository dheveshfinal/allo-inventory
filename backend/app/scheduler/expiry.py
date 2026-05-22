from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.core.database import AsyncSessionLocal
from app.modules.reservations.service import release_expired_reservations
import logging

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def _run_expiry():
    """Runs inside the scheduler every 2 minutes to clean up expired reservations."""
    async with AsyncSessionLocal() as db:
        try:
            released = await release_expired_reservations(db)
            if released > 0:
                logger.info(f"Released {released} expired reservation(s)")
        except Exception as e:
            logger.error(f"Error during expiry cleanup: {e}")


def start_scheduler():
    scheduler.add_job(_run_expiry, "interval", minutes=2, id="expiry_cleanup")
    scheduler.start()
    logger.info("APScheduler started — expiry job runs every 2 minutes")


def stop_scheduler():
    scheduler.shutdown(wait=False)
    logger.info("APScheduler stopped")
