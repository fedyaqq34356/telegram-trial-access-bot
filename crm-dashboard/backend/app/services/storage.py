"""Безопасное хранение файлов вне web-root (фото заявок, скрины отзывов).

Фото девушек НЕ должны быть публично доступны — лежат в private_uploads/,
отдаются только через авторизованные CRM-эндпоинты. Скрины отзывов публичны.
"""
import logging
import mimetypes
import uuid
from pathlib import Path

logger = logging.getLogger(__name__)

# backend/  (parents[2] = app/services/storage.py -> app -> backend)
BASE_DIR = Path(__file__).resolve().parents[2]
PRIVATE_ROOT = BASE_DIR / "private_uploads"
APPLICATIONS_DIR = PRIVATE_ROOT / "applications"
TESTIMONIALS_DIR = PRIVATE_ROOT / "testimonials"
LESSONS_DIR = PRIVATE_ROOT / "lessons"
VIDEOS_DIR = PRIVATE_ROOT / "videos"
APPS_DIR = PRIVATE_ROOT / "apps"

ALLOWED_VIDEO_EXT = {".mp4", ".webm", ".mov", ".m4v", ".ogg"}
MAX_VIDEO_BYTES = 300 * 1024 * 1024   # 300 МБ на видео
MAX_APK_BYTES = 500 * 1024 * 1024     # 500 МБ на APK

ALLOWED_EXT = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif"}
# что Telegram точно показывает как фото (heic не шлём в ТГ)
TELEGRAM_SAFE_EXT = {".jpg", ".jpeg", ".png", ".webp"}
MAX_BYTES = 8 * 1024 * 1024   # 8 МБ на файл
MAX_FILES = 3
MIN_FILES = 2


class UploadError(Exception):
    pass


def _ext_of(filename: str, content_type: str | None) -> str:
    ext = Path(filename or "").suffix.lower()
    if ext in ALLOWED_EXT:
        return ".jpg" if ext == ".jpeg" else ext
    guessed = mimetypes.guess_extension(content_type or "") or ""
    guessed = guessed.lower()
    if guessed in ALLOWED_EXT:
        return ".jpg" if guessed == ".jpeg" else guessed
    raise UploadError("Недопустимый формат файла. Разрешены: JPG, PNG, WebP, HEIC.")


def save_photos(subdir: Path, items: list[tuple[str, str | None, bytes]]) -> list[str]:
    """items: список (filename, content_type, data). Возвращает относительные пути от PRIVATE_ROOT."""
    subdir.mkdir(parents=True, exist_ok=True)
    saved: list[str] = []
    for filename, content_type, data in items:
        if len(data) > MAX_BYTES:
            raise UploadError("Файл слишком большой (макс. 8 МБ).")
        if not data:
            continue
        ext = _ext_of(filename, content_type)
        name = f"{uuid.uuid4().hex}{ext}"
        path = subdir / name
        path.write_bytes(data)
        saved.append(str(path.relative_to(PRIVATE_ROOT)))
    return saved


def save_application_photos(app_id: int, items: list[tuple[str, str | None, bytes]]) -> list[str]:
    if len(items) < MIN_FILES:
        raise UploadError("Загрузите минимум 2 фотографии.")
    if len(items) > MAX_FILES:
        raise UploadError("Можно загрузить не более 3 фотографий.")
    return save_photos(APPLICATIONS_DIR / str(app_id), items)


def save_testimonial_screenshot(item: tuple[str, str | None, bytes]) -> str:
    paths = save_photos(TESTIMONIALS_DIR, [item])
    if not paths:
        raise UploadError("Пустой файл.")
    return paths[0]


def save_lesson_image(item: tuple[str, str | None, bytes]) -> str:
    """Картинка к шагу обучения (публичная)."""
    paths = save_photos(LESSONS_DIR, [item])
    if not paths:
        raise UploadError("Пустой файл.")
    return paths[0]


def save_video(item: tuple[str, str | None, bytes]) -> str:
    """Видео (обучение / пример в заявке). Публичное, отдаётся напрямую."""
    filename, content_type, data = item
    if not data:
        raise UploadError("Пустой файл.")
    if len(data) > MAX_VIDEO_BYTES:
        raise UploadError("Видео слишком большое (макс. 300 МБ).")
    ext = Path(filename or "").suffix.lower()
    if ext not in ALLOWED_VIDEO_EXT:
        guessed = (mimetypes.guess_extension(content_type or "") or "").lower()
        ext = guessed if guessed in ALLOWED_VIDEO_EXT else ""
    if ext not in ALLOWED_VIDEO_EXT:
        raise UploadError("Недопустимый формат видео. Разрешены: MP4, WebM, MOV.")
    VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
    name = f"{uuid.uuid4().hex}{ext}"
    path = VIDEOS_DIR / name
    path.write_bytes(data)
    return str(path.relative_to(PRIVATE_ROOT))


def save_app_file(item: tuple[str, str | None, bytes]) -> str:
    """APK-файл приложения для скачивания. Публичный."""
    filename, content_type, data = item
    if not data:
        raise UploadError("Пустой файл.")
    if len(data) > MAX_APK_BYTES:
        raise UploadError("Файл слишком большой (макс. 500 МБ).")
    ext = Path(filename or "").suffix.lower()
    if ext != ".apk":
        raise UploadError("Допустим только файл APK.")
    APPS_DIR.mkdir(parents=True, exist_ok=True)
    name = f"{uuid.uuid4().hex}{ext}"
    path = APPS_DIR / name
    path.write_bytes(data)
    return str(path.relative_to(PRIVATE_ROOT))


def abs_path(rel: str) -> Path:
    """Преобразует относительный путь в абсолютный, защищаясь от выхода за PRIVATE_ROOT."""
    p = (PRIVATE_ROOT / rel).resolve()
    if not str(p).startswith(str(PRIVATE_ROOT.resolve())):
        raise UploadError("Недопустимый путь.")
    return p


def content_type_of(rel: str) -> str:
    return mimetypes.guess_type(rel)[0] or "application/octet-stream"


def is_telegram_safe(rel: str) -> bool:
    return Path(rel).suffix.lower() in TELEGRAM_SAFE_EXT
