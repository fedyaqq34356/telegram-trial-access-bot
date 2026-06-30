"""Автообновление данных по расписанию (APScheduler)."""
import logging

from apscheduler.schedulers.background import BackgroundScheduler

from ..database import SessionLocal
from . import app_settings
from .sync_service import sync_all

logger = logging.getLogger(__name__)

_scheduler: BackgroundScheduler | None = None

def _job():
    db = SessionLocal()
    try:
        results = sync_all(db)
        logger.info(f"Scheduled sync done: {results}")
    except Exception as e:
        logger.error(f"Scheduled sync error: {e}")
    finally:
        db.close()

def start_scheduler():
    global _scheduler
    if _scheduler is not None:
        return _scheduler

    db = SessionLocal()
    try:
        interval = int(float(app_settings.get_setting(db, "sync_interval_minutes")))
    except Exception:
        interval = 15
    finally:
        db.close()

    interval = max(1, interval)
    _scheduler = BackgroundScheduler(timezone="UTC")
    _scheduler.add_job(_job, "interval", minutes=interval, id="sync_all", max_instances=1, coalesce=True)
    _scheduler.start()
    logger.info(f"Scheduler started, interval={interval}min")
    return _scheduler

def reschedule(interval_minutes: int):
    if _scheduler is None:
        return
    interval_minutes = max(1, interval_minutes)
    _scheduler.reschedule_job("sync_all", trigger="interval", minutes=interval_minutes)
    logger.info(f"Scheduler rescheduled to {interval_minutes}min")

def shutdown_scheduler():
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
