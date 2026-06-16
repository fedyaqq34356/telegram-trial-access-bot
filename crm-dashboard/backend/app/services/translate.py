"""Бесплатный авто-перевод текста через публичный эндпоинт Google Translate.

Используется при сохранении FAQ и отзывов в CRM «Мой сайт»: админ вписывает
текст на одном языке, а мы переводим на остальные (ru/en/ua).
Ключ не нужен. При ошибке возвращаем исходный текст (не падаем).
"""
import logging

import requests

logger = logging.getLogger(__name__)

LANGS = ("ru", "en", "ua")
# наши коды → коды Google (украинский у Google = "uk")
_GOOGLE_CODE = {"ru": "ru", "en": "en", "ua": "uk"}
_URL = "https://translate.googleapis.com/translate_a/single"


def translate(text: str, target: str, source: str = "auto") -> str:
    """Переводит text на target ('ru'|'en'|'ua'). При ошибке вернёт исходный текст."""
    text = (text or "").strip()
    if not text:
        return ""
    tl = _GOOGLE_CODE.get(target, target)
    sl = _GOOGLE_CODE.get(source, source)
    try:
        r = requests.get(
            _URL,
            params={"client": "gtx", "sl": sl, "tl": tl, "dt": "t", "q": text},
            timeout=12,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        r.raise_for_status()
        data = r.json()
        # data[0] — список сегментов [[перевод, оригинал, ...], ...]
        return "".join(seg[0] for seg in data[0] if seg and seg[0]) or text
    except Exception as e:  # noqa: BLE001 — перевод не критичен
        logger.warning("translate failed (%s→%s): %s", source, target, e)
        return text


def to_trilang(text: str, source: str) -> dict:
    """{'ru':..,'en':..,'ua':..}. Для исходного языка берём текст как есть."""
    text = (text or "").strip()
    out = {}
    for lang in LANGS:
        out[lang] = text if lang == source else translate(text, lang, source)
    return out


def to_trilang_bulk(texts: list, source: str) -> dict:
    """Переводит много текстов сразу (параллельно, с дедупликацией).

    Возвращает {текст: {ru,en,ua}}. Быстро и без сотен последовательных
    запросов — чтобы не упираться в таймаут и rate-limit Google.
    """
    from concurrent.futures import ThreadPoolExecutor

    uniq = sorted({(t or "").strip() for t in texts if t and str(t).strip()})
    result = {t: {source: t} for t in uniq}
    targets = [lang for lang in LANGS if lang != source]
    jobs = [(t, lang) for t in uniq for lang in targets]

    def work(args):
        t, lang = args
        return t, lang, translate(t, lang, source)

    if jobs:
        with ThreadPoolExecutor(max_workers=8) as ex:
            for t, lang, val in ex.map(work, jobs):
                result[t][lang] = val
    for t in uniq:
        for lang in LANGS:
            result[t].setdefault(lang, t)
    return result
