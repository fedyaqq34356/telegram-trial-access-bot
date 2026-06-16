"""Логика уровней и системы риска. Уровень считается по заработку за 30 дней."""

GRADE_ORDER = ["S", "A", "B", "C", "D"]


def is_host_blocked(ban_status) -> bool:
    """Halo BanStatus: '2' = Normal (активна), '1' = Blocked (заблокирована).

    Активных показываем, заблокированных по умолчанию скрываем.
    Логика вынесена в одну функцию — при необходимости легко поменять трактовку.
    """
    return str(ban_status or "").strip() == "1"

GRADE_EMOJI = {"S": "💎", "A": "🌟", "B": "✨", "C": "🌸", "D": "🥀"}
GRADE_COLOR = {"S": "diamond", "A": "green", "B": "blue", "C": "orange", "D": "red"}


def compute_grade(monthly_income: int, grade_config: dict) -> str:
    income = int(monthly_income or 0)
    # идём от высшего к низшему
    ordered = sorted(grade_config.items(), key=lambda kv: kv[1].get("min", 0), reverse=True)
    for grade, cfg in ordered:
        if income >= cfg.get("min", 0):
            return grade
    return "D"


def income_range_label(grade: str, grade_config: dict) -> str:
    cfg = grade_config.get(grade, {})
    lo = cfg.get("min", 0)
    # найти следующий более высокий min
    higher = [c.get("min", 0) for g, c in grade_config.items() if c.get("min", 0) > lo]
    if not higher:
        return f"{lo:,}+".replace(",", " ")
    hi = min(higher) - 1
    return f"{lo:,} – {hi:,}".replace(",", " ")


def compute_risk(grade: str, real_down_rate: float, grade_config: dict, warning_threshold: float = 0.9) -> dict:
    """Возвращает статус риска: safe | warning | danger с причиной."""
    cfg = grade_config.get(grade, {})
    limit = cfg.get("limit")
    punishment = cfg.get("punishment")
    rate = float(real_down_rate or 0)

    if limit is None:
        return {
            "status": "safe",
            "limit": None,
            "excess": None,
            "punishment": punishment,
            "reason": f"Для уровня {grade} лимит коэффициента не задан.",
        }

    limit = float(limit)
    warn_from = round(limit * warning_threshold, 4)

    if rate >= limit:
        return {
            "status": "danger",
            "limit": limit,
            "excess": round(rate - limit, 4),
            "punishment": punishment,
            "reason": (
                f"Коэфф. за 30 дней {rate} превышает лимит уровня {grade} ({limit}). "
                f"Возможное наказание: {punishment}."
            ),
        }
    if rate >= warn_from:
        return {
            "status": "warning",
            "limit": limit,
            "excess": round(rate - limit, 4),
            "punishment": punishment,
            "reason": f"Коэфф. за 30 дней {rate} близко к лимиту уровня {grade} ({limit}).",
        }
    return {
        "status": "safe",
        "limit": limit,
        "excess": round(rate - limit, 4),
        "punishment": punishment,
        "reason": f"Коэфф. за 30 дней ниже лимита уровня {grade} ({limit}).",
    }


def enrich_host(host_dict: dict, grade_config: dict, coins_per_usd: float, warning_threshold: float = 0.9) -> dict:
    """Добавляет к данным девушки вычисленные поля: уровень, риск, usd-значения."""
    monthly = int(host_dict.get("monthly_income") or 0)
    grade = compute_grade(monthly, grade_config)
    risk = compute_risk(grade, host_dict.get("real_down_rate") or 0, grade_config, warning_threshold)
    cfg = grade_config.get(grade, {})

    def usd(coins):
        return round(float(coins or 0) / coins_per_usd, 2)

    # доход агентства считается из ТЕКУЩЕГО процента девушки (ratio хранится *100: 2000 = 20%)
    ratio = int(host_dict.get("ratio") or 0)
    agency_frac = ratio / 10000.0
    yest_gross = int(host_dict.get("last_day_income") or 0)
    month_agency = round(monthly * agency_frac)
    month_host = monthly - month_agency           # чистый заработок девушки за месяц
    yest_agency = round(yest_gross * agency_frac)
    yest_host = yest_gross - yest_agency           # чистый заработок девушки за вчера

    enriched = dict(host_dict)
    enriched.update({
        "grade": grade,
        "grade_emoji": GRADE_EMOJI.get(grade, ""),
        "grade_color": GRADE_COLOR.get(grade, "gray"),
        "grade_range": income_range_label(grade, grade_config),
        "grade_limit": cfg.get("limit"),
        "punishment": cfg.get("punishment"),
        "risk_status": risk["status"],
        "risk_reason": risk["reason"],
        "risk_excess": risk["excess"],
        "is_blocked": is_host_blocked(host_dict.get("ban_status")),
        # полный (gross) заработок — оставляем для справки
        "monthly_income_usd": usd(monthly),
        "last_day_income_usd": usd(host_dict.get("last_day_income")),
        "weekly_income_usd": usd(host_dict.get("weekly_income")),
        "balance_usd": usd(host_dict.get("balance_coins")),
        # чистый заработок девушки (после вычета % агентства)
        "month_income_host": month_host,
        "month_income_host_usd": usd(month_host),
        "last_day_income_host": yest_host,
        "last_day_income_host_usd": usd(yest_host),
        # доход агентства
        "month_income_agency": month_agency,
        "month_income_agency_usd": usd(month_agency),
        "last_day_income_agency": yest_agency,
        "last_day_income_agency_usd": usd(yest_agency),
    })
    return enriched
