from __future__ import annotations

from datetime import date, timedelta
import re
from dateutil.parser import parse as dt_parse
from dateutil.relativedelta import relativedelta


WEEKDAYS = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}

WORD_NUMS = {
    "a": 1,
    "an": 1,
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
}


def _normalize(s: str) -> str:
    s = s.strip().lower()
    s = s.replace(",", " ")

    # convert word numbers -> digits
    pattern = r"\b(" + "|".join(map(re.escape, WORD_NUMS.keys())) + r")\b"
    return re.sub(pattern, lambda m: str(WORD_NUMS[m.group(0)]), s)


def parse(s: str, today: date | None = None) -> date:
    if today is None:
        today = date.today()

    s = _normalize(s)

    # -------------------------
    # simple keywords
    # -------------------------
    if s == "today":
        return today
    if s == "tomorrow":
        return today + timedelta(days=1)
    if s == "yesterday":
        return today - timedelta(days=1)

    # -------------------------
    # next / last weekday
    # -------------------------
    m = re.fullmatch(r"next (\w+)", s)
    if m:
        return _next_weekday(today, m.group(1))

    m = re.fullmatch(r"last (\w+)", s)
    if m:
        return _last_weekday(today, m.group(1))

    # -------------------------
    # in X units
    # -------------------------
    m = re.fullmatch(r"in (\d+) (day|week|month|year)s?", s)
    if m:
        return today + _delta(int(m.group(1)), m.group(2))

    # -------------------------
    # X units from now
    # -------------------------
    m = re.fullmatch(r"(\d+) (day|week|month|year)s? from now", s)
    if m:
        return today + _delta(int(m.group(1)), m.group(2))

    # -------------------------
    # X units ago
    # -------------------------
    m = re.fullmatch(r"(\d+) (day|week|month|year)s? ago", s)
    if m:
        return today - _delta(int(m.group(1)), m.group(2))

    # -------------------------
    # COMPOUND (IMPORTANT FIX)
    # supports:
    # "2 years, 3 months before dec 1 2025"
    # "2 years 3 months after ..."
    # -------------------------
    m = re.fullmatch(
        r"(\d+)\s*years?\s*(?:,\s*)?(\d+)\s*months?\s*(before|after)\s+(.+)",
        s,
    )
    if m:
        years = int(m.group(1))
        months = int(m.group(2))
        direction = m.group(3)
        base = parse(m.group(4), today)

        delta = relativedelta(years=years, months=months)

        return base - delta if direction == "before" else base + delta

    # -------------------------
    # general relative before/after
    # -------------------------
    m = re.fullmatch(r"(\d+) (day|week|month|year)s? (before|after) (.+)", s)
    if m:
        amount = int(m.group(1))
        unit = m.group(2)
        direction = m.group(3)
        base = parse(m.group(4), today)

        delta = _delta(amount, unit)

        return base - delta if direction == "before" else base + delta

    # -------------------------
    # fallback: dateutil
    # -------------------------
    try:
        return dt_parse(s).date()
    except Exception:
        raise ValueError(f"Could not parse date string: {s}")


# -------------------------
# helpers
# -------------------------
def _delta(amount: int, unit: str):
    if unit == "day":
        return timedelta(days=amount)
    if unit == "week":
        return timedelta(weeks=amount)
    if unit == "month":
        return relativedelta(months=amount)
    if unit == "year":
        return relativedelta(years=amount)
    raise ValueError(unit)


def _next_weekday(today: date, weekday: str) -> date:
    weekday = weekday.lower()
    if weekday not in WEEKDAYS:
        raise ValueError(weekday)

    target = WEEKDAYS[weekday]
    diff = (target - today.weekday() + 7) % 7
    if diff == 0:
        diff = 7
    return today + timedelta(days=diff)


def _last_weekday(today: date, weekday: str) -> date:
    weekday = weekday.lower()
    if weekday not in WEEKDAYS:
        raise ValueError(weekday)

    target = WEEKDAYS[weekday]
    diff = (today.weekday() - target + 7) % 7
    if diff == 0:
        diff = 7
    return today - timedelta(days=diff)