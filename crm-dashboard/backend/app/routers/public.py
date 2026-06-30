"""Публичные эндпоинты для сайта tos-site (без авторизации).

Защита: honeypot-поле, простой in-memory rate-limit по IP, валидация обязательных полей.
"""
import json
import logging
import time

from fastapi import (
    APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Request, UploadFile,
)
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..deps import client_ip
from ..models import Application, ApplicationStatusEvent, Host, Testimonial, TrainingAccess, TrainingProgress
from ..services import app_settings, levels, storage, telegram_notify
from ..services.applications_service import build_notification_text

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/public", tags=["public"])

_submits: dict[str, list[float]] = {}
RATE_WINDOW = 3600.0
RATE_MAX = 5

def _rate_ok(ip: str) -> bool:
    now = time.time()
    hist = [t for t in _submits.get(ip, []) if now - t < RATE_WINDOW]
    _submits[ip] = hist
    if len(hist) >= RATE_MAX:
        return False
    hist.append(now)
    return True

def _truthy(v: str) -> bool:
    return str(v).strip().lower() in ("1", "true", "yes", "on", "да", "y")

@router.post("/applications")
async def submit_application(
    request: Request,
    background: BackgroundTasks,
    age: str = Form(""),
    country: str = Form(""),
    contact_telegram: str = Form(""),
    contact_whatsapp: str = Form(""),
    email: str = Form(""),
    experience: str = Form("false"),
    experience_apps: str = Form(""),
    time_commitment: str = Form(""),
    website: str = Form(""),
    photos: list[UploadFile] = File(default=[]),
    db: Session = Depends(get_db),
):
    if website.strip():
        return {"ok": True, "id": 0}

    ip = client_ip(request)
    if not _rate_ok(ip):
        raise HTTPException(status_code=429, detail="Слишком много заявок. Попробуйте позже.")

    try:
        age_int = int(float(age))
    except Exception:
        raise HTTPException(status_code=400, detail="Укажите корректный возраст.")
    if age_int < 16 or age_int > 40:
        raise HTTPException(status_code=400, detail="Возраст должен быть от 16 до 40.")
    if not country.strip():
        raise HTTPException(status_code=400, detail="Укажите страну.")
    if not (contact_telegram.strip() or contact_whatsapp.strip()):
        raise HTTPException(status_code=400, detail="Укажите Telegram или WhatsApp для связи.")

    items = []
    for f in photos or []:
        data = await f.read()
        if data:
            items.append((f.filename or "photo", f.content_type, data))

    app_row = Application(
        age=age_int,
        country=country.strip()[:120],
        contact_telegram=contact_telegram.strip()[:255],
        contact_whatsapp=contact_whatsapp.strip()[:64],
        email=email.strip()[:255],
        experience=_truthy(experience),
        experience_apps=experience_apps.strip(),
        time_commitment=time_commitment.strip()[:255],
        status="new",
        source="site",
    )
    db.add(app_row)
    db.commit()
    db.refresh(app_row)

    try:
        rel_paths = storage.save_application_photos(app_row.id, items)
    except storage.UploadError as e:
        db.delete(app_row)
        db.commit()
        raise HTTPException(status_code=400, detail=str(e))

    app_row.photos_json = json.dumps(rel_paths)
    db.add(ApplicationStatusEvent(application_id=app_row.id, old_status="", new_status="new", actor="сайт"))
    db.commit()
    db.refresh(app_row)

    owner = app_settings.get_setting(db, "owner_telegram_id") or str(settings.owner_telegram_id or "")
    tg_safe = [str(storage.abs_path(p)) for p in rel_paths if storage.is_telegram_safe(p)]
    background.add_task(
        telegram_notify.notify_new_application,
        token=settings.bot_token,
        owner_id=owner,
        text=build_notification_text(app_row),
        photo_paths=tg_safe,
        app_id=app_row.id,
        telegram=app_row.contact_telegram,
        whatsapp=app_row.contact_whatsapp,
    )
    return {"ok": True, "id": app_row.id}

@router.get("/site-content")
def site_content(db: Session = Depends(get_db)):
    """Публичный контент для сайта: соцсети, FAQ-оверрайды, видимые отзывы, текст-оверрайды."""
    def _json(key, fallback):
        try:
            return json.loads(app_settings.get_setting(db, key) or fallback)
        except Exception:
            return json.loads(fallback)

    faq_raw = _json("faq_json", "[]")
    faq_ml = {"ru": [], "en": [], "ua": []}
    for it in (faq_raw if isinstance(faq_raw, list) else []):
        q, a = it.get("q"), it.get("a")
        for lang in ("ru", "en", "ua"):
            qq = q.get(lang, "") if isinstance(q, dict) else (q or "")
            aa = a.get(lang, "") if isinstance(a, dict) else (a or "")
            if qq or aa:
                faq_ml[lang].append({"q": qq, "a": aa})

    from .site_content import lesson_resolve
    instr_raw = _json("instruction_steps_json", "[]")
    instruction = {lang: [lesson_resolve(l, lang) for l in (instr_raw if isinstance(instr_raw, list) else [])]
                   for lang in ("ru", "en", "ua")}
    imp_raw = _json("instruction_important_json", "[]")
    instruction_important = {lang: [(it.get(lang, "") if isinstance(it, dict) else (it or ""))
                                    for it in (imp_raw if isinstance(imp_raw, list) else [])]
                             for lang in ("ru", "en", "ua")}

    reviews = (
        db.query(Testimonial)
        .filter(Testimonial.is_visible == True)
        .order_by(Testimonial.sort_order, Testimonial.id.desc())
        .all()
    )
    review_out = []
    for t in reviews:
        try:
            d = json.loads(t.data_json) if t.data_json else None
        except Exception:
            d = None
        if not d:
            continue
        review_out.append({
            "id": t.id,
            "flag": d.get("flag", ""),
            "age": d.get("age", 0),
            "week": d.get("week", ""),
            "month": d.get("month", ""),
            "time_in": d.get("time_in", "20:15"),
            "time_reply": d.get("time_reply", "20:16"),
            "country": d.get("country", {}),
            "date": d.get("date", {}),
            "msg_in": d.get("msg_in", {}),
            "msg_reply": d.get("msg_reply", {}),
        })

    return {
        "social": {
            "telegram": app_settings.get_setting(db, "social_telegram"),
            "instagram": app_settings.get_setting(db, "social_instagram"),
            "tiktok": app_settings.get_setting(db, "social_tiktok"),
            "whatsapp": app_settings.get_setting(db, "social_whatsapp"),
        },
        "faq": faq_ml,
        "text_overrides": _json("site_text_overrides_json", "{}"),
        "reviews": review_out,
        "apply_example_video": _json("apply_example_video_json", "{}"),
        "app_downloads": _resolve_downloads(_json("app_downloads_json", "{}")),
        "instruction": instruction,
        "instruction_important": instruction_important,
    }

def _resolve_downloads(cfg: dict) -> dict:
    """slot → {type, href}. Для apk href = публичный эндпоинт скачивания."""
    out = {}
    for slot in ("android_female", "android_male", "iphone_female", "iphone_male"):
        s = cfg.get(slot) or {}
        typ = s.get("type", "link")
        if typ == "apk" and s.get("file"):
            href = f"/api/public/app-file/{s['file']}"
        elif typ == "link":
            href = (s.get("url") or "").strip()
        else:
            href = ""
        out[slot] = {"type": typ, "href": href}
    return out

@router.get("/testimonial-photo/{tid}")
def testimonial_photo(tid: int, db: Session = Depends(get_db)):
    t = db.get(Testimonial, tid)
    if not t or not t.is_visible or not t.screenshot_path:
        raise HTTPException(status_code=404, detail="Не найдено")
    try:
        path = storage.abs_path(t.screenshot_path)
    except storage.UploadError:
        raise HTTPException(status_code=404, detail="Не найдено")
    if not path.exists():
        raise HTTPException(status_code=404, detail="Не найдено")
    return FileResponse(path, media_type=storage.content_type_of(t.screenshot_path))

@router.post("/training/login")
def training_login(request: Request, payload: dict, db: Session = Depends(get_db)):
    """Вход на закрытую страницу «Обучение». Один пароль на всех."""
    password = str(payload.get("password", "")).strip()
    app_id = str(payload.get("app_id", "")).strip()
    real = app_settings.get_setting(db, "training_password")
    ok = bool(real) and password == real

    db.add(TrainingAccess(
        app_id_entered=app_id[:120],
        password_ok=ok,
        ip=client_ip(request),
        user_agent=request.headers.get("user-agent", "")[:500],
    ))
    db.commit()

    if not ok:
        raise HTTPException(status_code=401, detail="Неверный пароль")
    from .site_content import lesson_resolve

    def _ml(key):
        try:
            raw = json.loads(app_settings.get_setting(db, key) or "[]")
            return raw if isinstance(raw, list) else []
        except Exception:
            return []

    def _by_lang(rows):
        return {lang: [lesson_resolve(l, lang) for l in rows] for lang in ("ru", "en", "ua")}

    full = _ml("training_lessons_json")
    quick = _ml("training_lessons_quick_json")
    return {
        "ok": True,
        "lessons_full": _by_lang(full),
        "lessons_quick": _by_lang(quick),
    }

@router.post("/coefficient")
def coefficient_check(payload: dict, db: Session = Depends(get_db)):
    """Проверка коэффициента неприязни для девушки (по числовому Halo ID).

    Данные берутся из кеша CRM (таблица hosts, синхронизируется с панелями Halo) —
    та же информация, что показывает бот. Доступ — по паролю обучения.
    """
    password = str(payload.get("password", "")).strip()
    halo_id = str(payload.get("halo_id", "")).strip()
    real = app_settings.get_setting(db, "training_password")
    if not real or password != real:
        raise HTTPException(status_code=401, detail="Неверный пароль")
    if not halo_id.isdigit():
        raise HTTPException(status_code=400, detail="Введите числовой ID из приложения Halo")

    hosts = db.query(Host).filter(Host.display_account_id == halo_id).all()
    if not hosts:
        raise HTTPException(status_code=404, detail="ID не найден. Возможно, аккаунт ещё не синхронизирован — попробуйте позже или обратитесь к агенту.")
    host = max(hosts, key=lambda h: int(h.monthly_income or 0))

    host_dict = {
        "monthly_income": host.monthly_income,
        "weekly_income": host.weekly_income,
        "last_day_income": host.last_day_income,
        "down_rate": host.down_rate,
        "real_down_rate": host.real_down_rate,
        "ratio": host.ratio,
        "ban_status": host.ban_status,
    }
    grade_config = app_settings.get_grade_config(db)
    coins = app_settings.get_coins_per_usd(db)
    try:
        wt = float(app_settings.get_setting(db, "warning_threshold") or 0.9)
    except Exception:
        wt = 0.9
    enriched = levels.enrich_host(host_dict, grade_config, coins, wt)
    grade = enriched["grade"]
    down = float(host.down_rate or 0)
    real_down = float(host.real_down_rate or 0)
    grade_limit = enriched.get("grade_limit")
    return {
        "id": host.display_account_id,
        "agency": host.agent_name,
        "ranking": host.monthly_income_ranking,
        "grade": grade,
        "monthly_income": int(host.monthly_income or 0),
        "down_rate": round(down, 4),
        "real_down_rate": round(real_down, 4),
        "profile_ok": down < 0.18,
        "monthly_ok": grade_limit is None or real_down < float(grade_limit),
        "grade_limit": grade_limit,
        "risk_status": enriched["risk_status"],
        "blocked": enriched["is_blocked"],
    }

@router.get("/lesson-image/{rel:path}")
def lesson_image(rel: str):
    """Публичная отдача картинки шага обучения (lessons/<uuid>.<ext>)."""
    if not rel.startswith("lessons/"):
        raise HTTPException(status_code=404, detail="Не найдено")
    try:
        path = storage.abs_path(rel)
    except storage.UploadError:
        raise HTTPException(status_code=404, detail="Не найдено")
    if not path.exists():
        raise HTTPException(status_code=404, detail="Не найдено")
    return FileResponse(path, media_type=storage.content_type_of(rel))

@router.get("/media-video/{rel:path}")
def media_video(rel: str):
    """Публичная отдача видео (videos/<uuid>.<ext>). FileResponse поддерживает Range (перемотка)."""
    if not rel.startswith("videos/"):
        raise HTTPException(status_code=404, detail="Не найдено")
    try:
        path = storage.abs_path(rel)
    except storage.UploadError:
        raise HTTPException(status_code=404, detail="Не найдено")
    if not path.exists():
        raise HTTPException(status_code=404, detail="Не найдено")
    return FileResponse(path, media_type=storage.content_type_of(rel))

@router.get("/app-file/{rel:path}")
def app_file(rel: str):
    """Скачивание APK-файла (apps/<uuid>.apk). Отдаётся как вложение (скачивание)."""
    if not rel.startswith("apps/"):
        raise HTTPException(status_code=404, detail="Не найдено")
    try:
        path = storage.abs_path(rel)
    except storage.UploadError:
        raise HTTPException(status_code=404, detail="Не найдено")
    if not path.exists():
        raise HTTPException(status_code=404, detail="Не найдено")
    return FileResponse(
        path,
        media_type="application/vnd.android.package-archive",
        filename="app.apk",
    )

@router.post("/training/progress")
def training_progress(payload: dict, db: Session = Depends(get_db)):
    """Записывает прогресс прохождения обучения девушкой (по Halo ID). Доступ — по паролю обучения."""
    password = str(payload.get("password", "")).strip()
    halo_id = str(payload.get("halo_id", "")).strip()
    kind = str(payload.get("kind", "quick")).strip()
    real = app_settings.get_setting(db, "training_password")
    if not real or password != real:
        raise HTTPException(status_code=401, detail="Неверный пароль")
    if not halo_id or kind not in ("quick", "full"):
        return {"ok": False}
    done = int(payload.get("steps_done") or 0)
    total = int(payload.get("steps_total") or 0)
    completed = bool(payload.get("completed", False))

    row = db.query(TrainingProgress).filter(
        TrainingProgress.halo_id == halo_id[:64], TrainingProgress.kind == kind
    ).first()
    if row is None:
        row = TrainingProgress(halo_id=halo_id[:64], kind=kind)
        db.add(row)
    row.steps_done = max(row.steps_done or 0, done)
    row.steps_total = total or row.steps_total
    row.completed = row.completed or completed
    db.commit()
    return {"ok": True}
