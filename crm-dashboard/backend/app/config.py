from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "sqlite:///./crm.db"

    jwt_secret: str = "change-me-please-use-a-long-random-string"
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 15
    refresh_token_days: int = 7

    superadmin_username: str = "admin"
    superadmin_password: str = "admin123"
    superadmin_name: str = "Главный администратор"

    cors_origins: str = "http://localhost:3000"

    sync_interval_minutes: int = 15

    # ── интеграция с публичным сайтом и Telegram-ботом ──
    bot_token: str = ""                       # токен Telegram-бота для отправки уведомлений о заявках
    owner_telegram_id: int = 0                # запасной получатель (если не задан в настройках CRM)
    internal_api_token: str = "change-me-internal-token"  # секрет для вызовов бот→CRM
    public_site_origin: str = "http://localhost:3001"     # origin сайта tos-site для CORS

    @property
    def cors_origin_list(self) -> list[str]:
        origins = [o.strip() for o in self.cors_origins.split(",") if o.strip()]
        if self.public_site_origin and self.public_site_origin not in origins:
            origins.append(self.public_site_origin.strip())
        return origins


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
