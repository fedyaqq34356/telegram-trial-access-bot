from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base

def utcnow() -> datetime:
    return datetime.now(timezone.utc)

class Agency(Base):
    __tablename__ = "agencies"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    url: Mapped[str] = mapped_column(String(255), default="https://admin.livegirl.me")
    account: Mapped[str] = mapped_column(String(255), default="")
    password: Mapped[str] = mapped_column(String(255), default="")
    aemail: Mapped[str] = mapped_column(String(255), default="")
    apassword: Mapped[str] = mapped_column(String(255), default="")
    tfa_required: Mapped[bool] = mapped_column(Boolean, default=False)
    totp_secret: Mapped[str] = mapped_column(String(255), default="")

    phpsessid: Mapped[str] = mapped_column(String(255), default="")
    acuid: Mapped[str] = mapped_column(String(255), default="")
    cookies_json: Mapped[str] = mapped_column(Text, default="")
    session_updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    withdrawable_coins: Mapped[int] = mapped_column(Integer, default=0)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_split_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    hosts: Mapped[list["Host"]] = relationship(back_populates="agency", cascade="all, delete-orphan")
    accesses: Mapped[list["UserAgencyAccess"]] = relationship(
        back_populates="agency", cascade="all, delete-orphan"
    )

class Host(Base):
    """Кеш данных девушек, полученных из Halo Live."""

    __tablename__ = "hosts"
    __table_args__ = (UniqueConstraint("agency_id", "display_account_id", name="uq_host_agency_display"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    agency_id: Mapped[int] = mapped_column(ForeignKey("agencies.id", ondelete="CASCADE"), index=True)

    display_account_id: Mapped[str] = mapped_column(String(64), index=True)
    account_id: Mapped[str] = mapped_column(String(64), default="")
    nickname: Mapped[str] = mapped_column(String(255), default="")
    avatar_url: Mapped[str] = mapped_column(Text, default="")
    agent_name: Mapped[str] = mapped_column(String(255), default="")
    email: Mapped[str] = mapped_column(String(255), default="")

    ratio: Mapped[int] = mapped_column(Integer, default=0)
    down_rate: Mapped[float] = mapped_column(Float, default=0.0)
    real_down_rate: Mapped[float] = mapped_column(Float, default=0.0)
    receive_rate: Mapped[float] = mapped_column(Float, default=0.0)

    monthly_income: Mapped[int] = mapped_column(Integer, default=0)
    weekly_income: Mapped[int] = mapped_column(Integer, default=0)
    last_day_income: Mapped[int] = mapped_column(Integer, default=0)

    monthly_online: Mapped[str] = mapped_column(String(64), default="")
    weekly_online: Mapped[str] = mapped_column(String(64), default="")
    last_day_online: Mapped[str] = mapped_column(String(64), default="")

    balance_coins: Mapped[int] = mapped_column(Integer, default=0)
    split_diamond: Mapped[int] = mapped_column(Integer, default=0)

    anchor_grade: Mapped[str] = mapped_column(String(8), default="")
    monthly_income_ranking: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ban_status: Mapped[str] = mapped_column(String(16), default="2")
    fake: Mapped[str] = mapped_column(String(32), default="")
    approval_date: Mapped[str] = mapped_column(String(64), default="")

    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

    agency: Mapped["Agency"] = relationship(back_populates="hosts")

class User(Base):
    """Пользователь CRM."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    name: Mapped[str] = mapped_column(String(255), default="")
    role: Mapped[str] = mapped_column(String(32), default="admin")
    can_manage_users: Mapped[bool] = mapped_column(Boolean, default=False)
    can_view_traffic: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    last_login: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    accesses: Mapped[list["UserAgencyAccess"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )

    @property
    def is_superadmin(self) -> bool:
        return self.role == "superadmin"

class UserAgencyAccess(Base):
    __tablename__ = "user_agency_access"
    __table_args__ = (UniqueConstraint("user_id", "agency_id", name="uq_user_agency"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    agency_id: Mapped[int] = mapped_column(ForeignKey("agencies.id", ondelete="CASCADE"), index=True)

    can_view: Mapped[bool] = mapped_column(Boolean, default=True)
    can_change_ratio: Mapped[bool] = mapped_column(Boolean, default=False)
    can_split: Mapped[bool] = mapped_column(Boolean, default=False)

    user: Mapped["User"] = relationship(back_populates="accesses")
    agency: Mapped["Agency"] = relationship(back_populates="accesses")

class SplitOperation(Base):
    __tablename__ = "split_operations"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    scope_label: Mapped[str] = mapped_column(String(255), default="")
    agency_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

    processed: Mapped[int] = mapped_column(Integer, default=0)
    skipped: Mapped[int] = mapped_column(Integer, default=0)
    errors: Mapped[int] = mapped_column(Integer, default=0)
    total_amount_coins: Mapped[int] = mapped_column(Integer, default=0)
    agency_amount_coins: Mapped[int] = mapped_column(Integer, default=0)

    status: Mapped[str] = mapped_column(String(32), default="running")
    details: Mapped[str] = mapped_column(Text, default="")

    started_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    duration_seconds: Mapped[float] = mapped_column(Float, default=0.0)

class ActionLog(Base):
    __tablename__ = "action_log"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    username: Mapped[str] = mapped_column(String(128), default="")
    agency_name: Mapped[str] = mapped_column(String(255), default="")
    action_type: Mapped[str] = mapped_column(String(64), default="")
    anchor_id: Mapped[str] = mapped_column(String(64), default="")
    target: Mapped[str] = mapped_column(String(255), default="")
    old_value: Mapped[str] = mapped_column(String(255), default="")
    new_value: Mapped[str] = mapped_column(String(255), default="")
    status: Mapped[str] = mapped_column(String(32), default="")
    message: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)

class SecurityLog(Base):
    __tablename__ = "security_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    username: Mapped[str] = mapped_column(String(128), default="")
    action: Mapped[str] = mapped_column(String(128), default="")
    ip_address: Mapped[str] = mapped_column(String(64), default="")
    user_agent: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)

class Setting(Base):
    __tablename__ = "settings"

    key: Mapped[str] = mapped_column(String(128), primary_key=True)
    value: Mapped[str] = mapped_column(Text, default="")

APPLICATION_STATUSES = [
    "new",
    "in_progress",
    "contacted",
    "approved",
    "rejected",
    "registered",
    "office_activated",
    "training",
    "working",
]

class Application(Base):
    __tablename__ = "applications"

    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)
    age: Mapped[int] = mapped_column(Integer, default=0)
    country: Mapped[str] = mapped_column(String(120), default="")
    contact_telegram: Mapped[str] = mapped_column(String(255), default="")
    contact_whatsapp: Mapped[str] = mapped_column(String(64), default="")
    email: Mapped[str] = mapped_column(String(255), default="")
    experience: Mapped[bool] = mapped_column(Boolean, default=False)
    experience_apps: Mapped[str] = mapped_column(Text, default="")
    time_commitment: Mapped[str] = mapped_column(String(255), default="")
    photos_json: Mapped[str] = mapped_column(Text, default="[]")
    status: Mapped[str] = mapped_column(String(32), default="new", index=True)
    manager_comment: Mapped[str] = mapped_column(Text, default="")
    source: Mapped[str] = mapped_column(String(64), default="site")
    utm_source: Mapped[str] = mapped_column(String(255), default="")
    utm_campaign: Mapped[str] = mapped_column(String(255), default="")
    visitor_id: Mapped[str] = mapped_column(String(64), default="", index=True)

    events: Mapped[list["ApplicationStatusEvent"]] = relationship(
        back_populates="application", cascade="all, delete-orphan",
        order_by="ApplicationStatusEvent.id",
    )

class ApplicationStatusEvent(Base):
    __tablename__ = "application_status_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    application_id: Mapped[int] = mapped_column(ForeignKey("applications.id", ondelete="CASCADE"), index=True)
    old_status: Mapped[str] = mapped_column(String(32), default="")
    new_status: Mapped[str] = mapped_column(String(32), default="")
    actor: Mapped[str] = mapped_column(String(120), default="")
    note: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    application: Mapped["Application"] = relationship(back_populates="events")

class Testimonial(Base):
    """Отзыв девушки (скрин ТГ-переписки) для публичного сайта."""
    __tablename__ = "testimonials"

    id: Mapped[int] = mapped_column(primary_key=True)
    country: Mapped[str] = mapped_column(String(120), default="")
    age: Mapped[int] = mapped_column(Integer, default=0)
    result_text: Mapped[str] = mapped_column(Text, default="")
    screenshot_path: Mapped[str] = mapped_column(Text, default="")
    data_json: Mapped[str] = mapped_column(Text, default="")
    is_visible: Mapped[bool] = mapped_column(Boolean, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

class TrainingAccess(Base):
    """Лог входов на закрытую страницу «Обучение» (для главного админа)."""
    __tablename__ = "training_access"

    id: Mapped[int] = mapped_column(primary_key=True)
    app_id_entered: Mapped[str] = mapped_column(String(120), default="")
    password_ok: Mapped[bool] = mapped_column(Boolean, default=False)
    ip: Mapped[str] = mapped_column(String(64), default="")
    user_agent: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)

class TrainingProgress(Base):
    """Прогресс прохождения обучения девушкой (по её Halo ID)."""
    __tablename__ = "training_progress"
    __table_args__ = (UniqueConstraint("halo_id", "kind", name="uq_progress_halo_kind"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    halo_id: Mapped[str] = mapped_column(String(64), index=True)
    kind: Mapped[str] = mapped_column(String(16), default="quick")
    steps_done: Mapped[int] = mapped_column(Integer, default=0)
    steps_total: Mapped[int] = mapped_column(Integer, default=0)
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow, index=True)

class PageVisit(Base):
    """Посещение страницы публичного сайта (свой трекер, без внешних сервисов)."""
    __tablename__ = "page_visits"

    id: Mapped[int] = mapped_column(primary_key=True)
    path: Mapped[str] = mapped_column(String(512), default="", index=True)
    referrer: Mapped[str] = mapped_column(String(512), default="")
    referrer_host: Mapped[str] = mapped_column(String(255), default="")

    utm_source: Mapped[str] = mapped_column(String(255), default="", index=True)
    utm_medium: Mapped[str] = mapped_column(String(255), default="")
    utm_campaign: Mapped[str] = mapped_column(String(255), default="", index=True)
    utm_content: Mapped[str] = mapped_column(String(255), default="")
    utm_term: Mapped[str] = mapped_column(String(255), default="")

    visitor_id: Mapped[str] = mapped_column(String(64), default="", index=True)
    is_unique: Mapped[bool] = mapped_column(Boolean, default=False)
    lang: Mapped[str] = mapped_column(String(8), default="")
    device: Mapped[str] = mapped_column(String(16), default="")

    ip: Mapped[str] = mapped_column(String(64), default="")
    user_agent: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)
