"""CRM «Мой сайт»: отзывы (Testimonial, Telegram-формат) и FAQ.

Отзывы и FAQ вводятся на одном языке, при сохранении авто-переводятся на
остальные (ru/en/ua) через services.translate. Тексты сайта/соцсети/пароль
обучения по-прежнему в k/v-настройках (/api/settings).
"""
import json
import logging

from fastapi import APIRouter, Body, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user, require_superadmin
from ..models import Testimonial, TrainingProgress, User
from ..services import app_settings, storage, translate

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/site-content", tags=["site-content"])

LANGS = ("ru", "en", "ua")


def _parse(t: Testimonial) -> dict:
    try:
        return json.loads(t.data_json) if t.data_json else {}
    except Exception:
        return {}


def _serialize(t: Testimonial) -> dict:
    """Для редактирования в CRM: отдаём значения на языке ввода (source_lang)."""
    d = _parse(t)
    src = d.get("source_lang", "ru")
    pick = lambda m: (m or {}).get(src, "") if isinstance(m, dict) else (m or "")
    return {
        "id": t.id,
        "is_visible": t.is_visible,
        "sort_order": t.sort_order,
        "lang": src,
        "flag": d.get("flag", ""),
        "country": pick(d.get("country")),
        "age": d.get("age", 0),
        "week": d.get("week", ""),
        "month": d.get("month", ""),
        "date": pick(d.get("date")),
        "msg_in": pick(d.get("msg_in")),
        "msg_reply": pick(d.get("msg_reply")),
        "time_in": d.get("time_in", ""),
        "time_reply": d.get("time_reply", ""),
        "created_at": t.created_at.isoformat() if t.created_at else None,
    }


def _build_data(p: dict) -> dict:
    """Из ввода админа строим мультиязычный data_json (переводим тексты)."""
    lang = p.get("lang", "ru")
    if lang not in LANGS:
        lang = "ru"
    return {
        "source_lang": lang,
        "flag": (p.get("flag") or "").strip(),
        "age": int(float(p.get("age") or 0)),
        "week": (p.get("week") or "").strip(),
        "month": (p.get("month") or "").strip(),
        "time_in": (p.get("time_in") or "").strip() or "20:15",
        "time_reply": (p.get("time_reply") or "").strip() or "20:16",
        "country": translate.to_trilang(p.get("country") or "", lang),
        "date": translate.to_trilang(p.get("date") or "", lang),
        "msg_in": translate.to_trilang(p.get("msg_in") or "", lang),
        "msg_reply": translate.to_trilang(p.get("msg_reply") or "", lang),
    }


# ─────────────────────────── отзывы ───────────────────────────
@router.get("/testimonials")
def list_testimonials(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.query(Testimonial).order_by(Testimonial.sort_order, Testimonial.id.desc()).all()
    return [_serialize(t) for t in rows]


@router.post("/testimonials")
def create_testimonial(p: dict = Body(...), admin: User = Depends(require_superadmin), db: Session = Depends(get_db)):
    data = _build_data(p)
    t = Testimonial(
        country=data["country"].get(data["source_lang"], "")[:120],
        age=data["age"],
        data_json=json.dumps(data, ensure_ascii=False),
        is_visible=bool(p.get("is_visible", True)),
        sort_order=int(float(p.get("sort_order") or 0)),
    )
    db.add(t)
    db.commit()
    db.refresh(t)
    return _serialize(t)


@router.put("/testimonials/{tid}")
def update_testimonial(tid: int, p: dict = Body(...), admin: User = Depends(require_superadmin), db: Session = Depends(get_db)):
    t = db.get(Testimonial, tid)
    if not t:
        raise HTTPException(status_code=404, detail="Отзыв не найден")
    # частичное обновление видимости/порядка без перевода
    if set(p.keys()) <= {"is_visible", "sort_order"}:
        if "is_visible" in p:
            t.is_visible = bool(p["is_visible"])
        if "sort_order" in p:
            t.sort_order = int(float(p["sort_order"] or 0))
    else:
        data = _build_data(p)
        t.country = data["country"].get(data["source_lang"], "")[:120]
        t.age = data["age"]
        t.data_json = json.dumps(data, ensure_ascii=False)
        if "is_visible" in p:
            t.is_visible = bool(p["is_visible"])
        if "sort_order" in p:
            t.sort_order = int(float(p["sort_order"] or 0))
    db.commit()
    db.refresh(t)
    return _serialize(t)


@router.delete("/testimonials/{tid}")
def delete_testimonial(tid: int, admin: User = Depends(require_superadmin), db: Session = Depends(get_db)):
    t = db.get(Testimonial, tid)
    if not t:
        raise HTTPException(status_code=404, detail="Отзыв не найден")
    db.delete(t)
    db.commit()
    return {"ok": True}


# ─────────────────────────── FAQ ───────────────────────────
def _load_faq(db: Session) -> list:
    try:
        raw = json.loads(app_settings.get_setting(db, "faq_json") or "[]")
        return raw if isinstance(raw, list) else []
    except Exception:
        return []


@router.get("/faq")
def get_faq(lang: str = "ru", user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Отдаёт вопросы на запрошенном языке (для редактирования в CRM)."""
    if lang not in LANGS:
        lang = "ru"
    items = []
    for it in _load_faq(db):
        q, a = it.get("q"), it.get("a")
        items.append({
            "q": q.get(lang, "") if isinstance(q, dict) else (q or ""),
            "a": a.get(lang, "") if isinstance(a, dict) else (a or ""),
        })
    return {"lang": lang, "items": items}


@router.put("/faq")
def put_faq(p: dict = Body(...), admin: User = Depends(require_superadmin), db: Session = Depends(get_db)):
    """Принимает {lang, items:[{q,a}]}, переводит на все языки и сохраняет."""
    lang = p.get("lang", "ru")
    if lang not in LANGS:
        lang = "ru"
    items = p.get("items") or []
    multilang = []
    for it in items:
        q = (it.get("q") or "").strip()
        a = (it.get("a") or "").strip()
        if not q and not a:
            continue
        multilang.append({"q": translate.to_trilang(q, lang), "a": translate.to_trilang(a, lang)})
    app_settings.set_setting(db, "faq_json", json.dumps(multilang, ensure_ascii=False))
    return get_faq(lang=lang, user=admin, db=db)


# ─────────────────────────── обучение: уроки (мультиязычные) ───────────────────────────
LESSON_SETTING = {"quick": "training_lessons_quick_json", "full": "training_lessons_json"}


def _lesson_pick(v, lang: str) -> str:
    return v.get(lang, "") if isinstance(v, dict) else (v or "")


def _image_pick(img, lang: str) -> str:
    """Картинка для языка: своя для lang, иначе RU, иначе любая непустая."""
    if isinstance(img, dict):
        return img.get(lang) or img.get("ru") or next((v for v in img.values() if v), "")
    return img or ""


def lesson_resolve(ml: dict, lang: str) -> dict:
    """Мультиязычный урок → урок на одном языке (для редактирования / отдачи)."""
    return {
        "type": ml.get("type", "text"),
        "url": ml.get("url", ""),
        "image": _image_pick(ml.get("image"), lang),
        "video": _image_pick(ml.get("video"), lang),  # видео тоже по языкам
        "title": _lesson_pick(ml.get("title"), lang),
        "body": _lesson_pick(ml.get("body"), lang),
        "note": _lesson_pick(ml.get("note"), lang),
        "items": [_lesson_pick(it, lang) for it in (ml.get("items") or [])],
    }


def _lesson_translate(lesson: dict, lang: str, cache: dict | None = None) -> dict:
    """Урок на языке lang → мультиязычный (переводим текстовые поля).

    cache — карта {текст: {ru,en,ua}} из to_trilang_bulk (если передана,
    переводы не дёргают сеть повторно)."""
    def tri(s):
        s = (s or "").strip()
        if not s:
            return {"ru": "", "en": "", "ua": ""}
        if cache is not None and s in cache:
            return cache[s]
        return translate.to_trilang(s, lang)

    items = [it for it in (lesson.get("items") or []) if str(it).strip()]
    return {
        "type": lesson.get("type", "text"),
        "url": (lesson.get("url") or "").strip(),
        "image": (lesson.get("image") or "").strip(),
        "video": (lesson.get("video") or "").strip(),
        "title": tri(lesson.get("title")),
        "body": tri(lesson.get("body")),
        "note": tri(lesson.get("note")),
        "items": [tri(it) for it in items],
    }


def _load_lessons(db: Session, kind: str) -> list:
    try:
        raw = json.loads(app_settings.get_setting(db, LESSON_SETTING[kind]) or "[]")
        return raw if isinstance(raw, list) else []
    except Exception:
        return []


@router.get("/training-lessons")
def get_training_lessons(kind: str = "quick", lang: str = "ru", user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if kind not in LESSON_SETTING:
        kind = "quick"
    if lang not in LANGS:
        lang = "ru"
    return {"kind": kind, "lang": lang, "lessons": [lesson_resolve(l, lang) for l in _load_lessons(db, kind)]}


@router.put("/training-lessons")
def put_training_lessons(p: dict = Body(...), admin: User = Depends(require_superadmin), db: Session = Depends(get_db)):
    """{kind, lang, lessons:[...]}: переводит тексты на все языки и сохраняет."""
    kind = p.get("kind", "quick")
    if kind not in LESSON_SETTING:
        kind = "quick"
    lang = p.get("lang", "ru")
    if lang not in LANGS:
        lang = "ru"
    lessons = p.get("lessons") or []
    existing = _load_lessons(db, kind)

    def _is_full(ml):  # уже мультиязычный словарь со всеми языками?
        return isinstance(ml, dict) and all(k in ml for k in LANGS)

    def _lang_val(ml):  # значение поля на языке ввода
        return (ml.get(lang, "") if isinstance(ml, dict) else (ml or "")).strip()

    def _ex(idx, field):
        return existing[idx].get(field) if idx < len(existing) else None

    # 1) собрать ТОЛЬКО изменённые тексты (по языку ввода) — их и переведём
    changed = []
    for idx, l in enumerate(lessons):
        for field in ("title", "body", "note"):
            cur = (l.get(field) or "").strip()
            ex = _ex(idx, field)
            if cur and not (_is_full(ex) and cur == _lang_val(ex)):
                changed.append(cur)
        items = [it for it in (l.get("items") or []) if str(it).strip()]
        ex_items = _ex(idx, "items") or []
        for k, it in enumerate(items):
            cur = it.strip()
            ex_it = ex_items[k] if k < len(ex_items) else None
            if cur and not (_is_full(ex_it) and cur == _lang_val(ex_it)):
                changed.append(cur)
    cache = translate.to_trilang_bulk(changed, lang)

    def tri(cur, ex):
        """Если текст на языке ввода не менялся — сохраняем прошлые переводы (не портим ручной текст)."""
        cur = (cur or "").strip()
        if _is_full(ex) and cur == _lang_val(ex):
            return ex
        if not cur:
            return {"ru": "", "en": "", "ua": ""}
        return cache.get(cur) or translate.to_trilang(cur, lang)

    multilang = []
    for idx, l in enumerate(lessons):
        items = [it for it in (l.get("items") or []) if str(it).strip()]
        ex_items = _ex(idx, "items") or []
        ml = {
            "type": l.get("type", "text"),
            "url": (l.get("url") or "").strip(),
            "title": tri(l.get("title"), _ex(idx, "title")),
            "body": tri(l.get("body"), _ex(idx, "body")),
            "note": tri(l.get("note"), _ex(idx, "note")),
            "items": [tri(it, ex_items[k] if k < len(ex_items) else None) for k, it in enumerate(items)],
        }
        # картинки/видео — по языкам: сохраняем версии других языков из прошлой записи
        for field in ("image", "video"):
            new_val = (l.get(field) or "").strip()
            old = _ex(idx, field)
            val_ml = dict(old) if isinstance(old, dict) else ({"ru": old, "en": old, "ua": old} if old else {})
            val_ml[lang] = new_val
            ml[field] = val_ml
        multilang.append(ml)

    app_settings.set_setting(db, LESSON_SETTING[kind], json.dumps(multilang, ensure_ascii=False))
    return get_training_lessons(kind=kind, lang=lang, user=admin, db=db)


# ─────────────────────────── обучение: картинки + прогресс ───────────────────────────
@router.post("/lesson-image")
async def upload_lesson_image(image: UploadFile = File(...), admin: User = Depends(require_superadmin)):
    """Загрузка картинки шага обучения. Возвращает относительный путь и публичный URL."""
    data = await image.read()
    if not data:
        raise HTTPException(status_code=400, detail="Пустой файл")
    try:
        rel = storage.save_lesson_image((image.filename or "img", image.content_type, data))
    except storage.UploadError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"path": rel, "url": f"/api/public/lesson-image/{rel}"}


@router.post("/lesson-video")
async def upload_lesson_video(video: UploadFile = File(...), admin: User = Depends(require_superadmin)):
    """Загрузка видео (обучение / пример в заявке). Возвращает путь и публичный URL."""
    data = await video.read()
    if not data:
        raise HTTPException(status_code=400, detail="Пустой файл")
    try:
        rel = storage.save_video((video.filename or "vid", video.content_type, data))
    except storage.UploadError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"path": rel, "url": f"/api/public/media-video/{rel}"}


@router.get("/training-progress")
def training_progress_list(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.query(TrainingProgress).order_by(TrainingProgress.updated_at.desc()).all()
    return [
        {
            "id": r.id,
            "halo_id": r.halo_id,
            "kind": r.kind,
            "steps_done": r.steps_done,
            "steps_total": r.steps_total,
            "percent": round(100 * r.steps_done / r.steps_total) if r.steps_total else (100 if r.completed else 0),
            "completed": r.completed,
            "updated_at": r.updated_at.isoformat() if r.updated_at else None,
        }
        for r in rows
    ]
