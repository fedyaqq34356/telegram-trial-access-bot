import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .database import Base, SessionLocal, engine
from .models import User
from .routers import (
    agencies,
    applications,
    auth,
    dashboard,
    hosts,
    logs,
    public,
    risk,
    settings as settings_router,
    site_content,
    split,
    sync,
    traffic,
    users,
    withdraw,
)
from .security import hash_password
from .services import app_settings, scheduler

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("crm")

def _ensure_columns():
    """Лёгкая миграция: create_all не добавляет НОВЫЕ колонки в уже существующие таблицы.
    Досоздаём недостающие через ALTER TABLE (идемпотентно)."""
    from sqlalchemy import inspect, text
    dt_type = "DATETIME" if engine.dialect.name == "sqlite" else "TIMESTAMP"
    bool_default = "0" if engine.dialect.name == "sqlite" else "FALSE"
    wanted = {
        "agencies": [("last_split_at", dt_type)],
        "testimonials": [("data_json", "TEXT")],
        "users": [("can_view_traffic", f"BOOLEAN DEFAULT {bool_default}")],
        "applications": [
            ("utm_source", "VARCHAR(255) DEFAULT ''"),
            ("utm_campaign", "VARCHAR(255) DEFAULT ''"),
            ("visitor_id", "VARCHAR(64) DEFAULT ''"),
        ],
    }
    insp = inspect(engine)
    with engine.begin() as conn:
        for table, cols in wanted.items():
            if not insp.has_table(table):
                continue
            existing = {c["name"] for c in insp.get_columns(table)}
            for name, ddl in cols:
                if name not in existing:
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {ddl}"))
                    logger.info(f"Миграция: добавлена колонка {table}.{name}")

def init_db():
    Base.metadata.create_all(bind=engine)
    _ensure_columns()
    db = SessionLocal()
    try:
        app_settings.ensure_defaults(db)
        if db.query(User).filter(User.role == "superadmin").count() == 0:
            superadmin = User(
                username=settings.superadmin_username,
                password_hash=hash_password(settings.superadmin_password),
                name=settings.superadmin_name,
                role="superadmin",
                can_manage_users=True,
            )
            db.add(superadmin)
            db.commit()
            logger.info(f"Создан главный администратор: {settings.superadmin_username}")
    finally:
        db.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    scheduler.start_scheduler()
    logger.info("CRM backend запущен")
    yield
    scheduler.shutdown_scheduler()

app = FastAPI(title="Tos Agency CRM", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for r in (auth, agencies, hosts, dashboard, risk, split, users, logs, settings_router, sync,
          public, applications, site_content, traffic, withdraw):
    app.include_router(r.router, prefix="/api")

app.include_router(applications.internal_router, prefix="/api")

@app.get("/api/health")
def health():
    return {"status": "ok"}
