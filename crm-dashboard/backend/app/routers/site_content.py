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

def _load_important(db: Session) -> list:
    try:
        raw = json.loads(app_settings.get_setting(db, "instruction_important_json") or "[]")
        return raw if isinstance(raw, list) else []
    except Exception:
        return []

@router.get("/instruction-important")
def get_important(lang: str = "ru", user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if lang not in LANGS:
        lang = "ru"
    items = [(it.get(lang, "") if isinstance(it, dict) else (it or "")) for it in _load_important(db)]
    return {"lang": lang, "items": items}

@router.put("/instruction-important")
def put_important(p: dict = Body(...), admin: User = Depends(require_superadmin), db: Session = Depends(get_db)):
    """{lang, items:[str]} — переводит каждый пункт на все языки и сохраняет (только изменённые)."""
    lang = p.get("lang", "ru")
    if lang not in LANGS:
        lang = "ru"
    incoming = [str(x).strip() for x in (p.get("items") or []) if str(x).strip()]
    existing = _load_important(db)

    def _full(ml):
        return isinstance(ml, dict) and all(k in ml for k in LANGS)
    changed = [cur for i, cur in enumerate(incoming)
               if not (i < len(existing) and _full(existing[i]) and cur == existing[i].get(lang, "").strip())]
    cache = translate.to_trilang_bulk(changed, lang)
    out = []
    for i, cur in enumerate(incoming):
        ex = existing[i] if i < len(existing) else None
        if _full(ex) and cur == ex.get(lang, "").strip():
            out.append(ex)
        else:
            out.append(cache.get(cur) or translate.to_trilang(cur, lang))
    app_settings.set_setting(db, "instruction_important_json", json.dumps(out, ensure_ascii=False))
    return get_important(lang=lang, user=admin, db=db)

LESSON_SETTING = {"quick": "training_lessons_quick_json", "full": "training_lessons_json", "instruction": "instruction_steps_json"}

def _lesson_pick(v, lang: str) -> str:
    return v.get(lang, "") if isinstance(v, dict) else (v or "")

def _image_pick(img, lang: str) -> str:
    """Картинка для языка: своя для lang, иначе RU, иначе любая непустая."""
    if isinstance(img, dict):
        return img.get(lang) or img.get("ru") or next((v for v in img.values() if v), "")
    return img or ""

CALLOUT_KINDS = ("tip", "important", "forbidden", "example")

def lesson_resolve(ml: dict, lang: str) -> dict:
    """Мультиязычный урок → урок на одном языке (для редактирования / отдачи)."""
    callouts_raw = ml.get("callouts")
    if callouts_raw:
        callouts = [{"kind": c.get("kind", "tip"), "text": _lesson_pick(c.get("text"), lang),
                     "langs": c.get("langs") if isinstance(c.get("langs"), list) else list(LANGS)}
                    for c in callouts_raw]
    else:
        note = _lesson_pick(ml.get("note"), lang)
        callouts = [{"kind": "tip", "text": note, "langs": list(LANGS)}] if note else []
    gallery = [{"image": _image_pick(g.get("image"), lang), "caption": _lesson_pick(g.get("caption"), lang)}
               for g in (ml.get("gallery") or [])]
    return {
        "type": ml.get("type", "text"),
        "url": ml.get("url", ""),
        "image": _image_pick(ml.get("image"), lang),
        "video": _image_pick(ml.get("video"), lang),
        "title": _lesson_pick(ml.get("title"), lang),
        "body": _lesson_pick(ml.get("body"), lang),
        "items": [_lesson_pick(it, lang) for it in (ml.get("items") or [])],
        "callouts": callouts,
        "gallery": gallery,
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

    def _is_full(ml):
        return isinstance(ml, dict) and all(k in ml for k in LANGS)

    def _lang_val(ml):
        return (ml.get(lang, "") if isinstance(ml, dict) else (ml or "")).strip()

    def _ex(idx, field):
        return existing[idx].get(field) if idx < len(existing) else None

    def _ex_callouts(idx):
        c = existing[idx].get("callouts") if idx < len(existing) else None
        return c if isinstance(c, list) else []

    changed = []
    for idx, l in enumerate(lessons):
        for field in ("title", "body"):
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
        ex_co = _ex_callouts(idx)
        callouts = [c for c in (l.get("callouts") or []) if (c.get("text") or "").strip()]
        for k, c in enumerate(callouts):
            cur = (c.get("text") or "").strip()
            ex_t = ex_co[k].get("text") if k < len(ex_co) else None
            if cur and not (_is_full(ex_t) and cur == _lang_val(ex_t)):
                changed.append(cur)
        ex_gal = existing[idx].get("gallery") if idx < len(existing) else None
        ex_gal = ex_gal if isinstance(ex_gal, list) else []
        for k, g in enumerate(l.get("gallery") or []):
            cur = (g.get("caption") or "").strip()
            ex_cap = ex_gal[k].get("caption") if k < len(ex_gal) else None
            if cur and not (_is_full(ex_cap) and cur == _lang_val(ex_cap)):
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
        ex_co = _ex_callouts(idx)
        callouts = [c for c in (l.get("callouts") or []) if (c.get("text") or "").strip()]
        ml = {
            "type": l.get("type", "text"),
            "url": (l.get("url") or "").strip(),
            "title": tri(l.get("title"), _ex(idx, "title")),
            "body": tri(l.get("body"), _ex(idx, "body")),
            "items": [tri(it, ex_items[k] if k < len(ex_items) else None) for k, it in enumerate(items)],
            "callouts": [
                {"kind": (c.get("kind") if c.get("kind") in CALLOUT_KINDS else "tip"),
                 "text": tri(c.get("text"), ex_co[k].get("text") if k < len(ex_co) else None),
                 "langs": ([x for x in (c.get("langs") or LANGS) if x in LANGS] or list(LANGS))}
                for k, c in enumerate(callouts)
            ],
        }
        for field in ("image", "video"):
            new_val = (l.get(field) or "").strip()
            old = _ex(idx, field)
            val_ml = dict(old) if isinstance(old, dict) else ({"ru": old, "en": old, "ua": old} if old else {})
            val_ml[lang] = new_val
            ml[field] = val_ml
        ex_gal = existing[idx].get("gallery") if idx < len(existing) else None
        ex_gal = ex_gal if isinstance(ex_gal, list) else []
        gallery = [g for g in (l.get("gallery") or []) if (g.get("image") or "").strip() or (g.get("caption") or "").strip()]
        ml["gallery"] = []
        for k, g in enumerate(gallery):
            ex_g = ex_gal[k] if k < len(ex_gal) and isinstance(ex_gal[k], dict) else {}
            img_new = (g.get("image") or "").strip()
            old_img = ex_g.get("image")
            img_ml = dict(old_img) if isinstance(old_img, dict) else ({"ru": old_img, "en": old_img, "ua": old_img} if old_img else {})
            img_ml[lang] = img_new
            ml["gallery"].append({"image": img_ml, "caption": tri(g.get("caption"), ex_g.get("caption"))})
        multilang.append(ml)

    app_settings.set_setting(db, LESSON_SETTING[kind], json.dumps(multilang, ensure_ascii=False))
    return get_training_lessons(kind=kind, lang=lang, user=admin, db=db)

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

@router.post("/app-file")
async def upload_app_file(file: UploadFile = File(...), admin: User = Depends(require_superadmin)):
    """Загрузка APK-файла приложения. Возвращает относительный путь."""
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Пустой файл")
    try:
        rel = storage.save_app_file((file.filename or "app.apk", file.content_type, data))
    except storage.UploadError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"path": rel, "url": f"/api/public/app-file/{rel}"}

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
