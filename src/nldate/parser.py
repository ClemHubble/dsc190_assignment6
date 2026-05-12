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

    # remove commas inside numbers like 1,000
    s = re.sub(r"(?<=\d),(?=\s*\d)", "", s)

    # normalize whitespace
    s = re.sub(r"\s+", " ", s)

    # convert word numbers
    pattern = r"\b(" + "|".join(map(re.escape, WORD_NUMS.keys())) + r")\b"
    s = re.sub(pattern, lambda m: str(WORD_NUMS[m.group(0)]), s)

    return s.strip()


def parse(s: str, today: date | None = None) -> date:
    """
    Parse natural language date expressions into datetime.date objects.
    """
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

    if s in {"the day after tomorrow", "day after tomorrow"}:
        return today + timedelta(days=2)

    if s in {"the day before yesterday", "day before yesterday"}:
        return today - timedelta(days=2)

    # -------------------------
    # next weekday
    # -------------------------
    match = re.fullmatch(r"next (\w+)", s)
    if match:
        return _next_weekday(today, match.group(1))

    # -------------------------
    # last weekday
    # -------------------------
    match = re.fullmatch(r"last (\w+)", s)
    if match:
        return _last_weekday(today, match.group(1))

    # -------------------------
    # in X units
    # -------------------------
    match = re.fullmatch(r"in (\d+) (day|week|month|year)s?", s)
    if match:
        amount = int(match.group(1))
        unit = match.group(2)
        return today + _make_delta(amount, unit)

    # -------------------------
    # X units ago
    # -------------------------
    match = re.fullmatch(r"(\d+) (day|week|month|year)s? ago", s)
    if match:
        amount = int(match.group(1))
        unit = match.group(2)
        return today - _make_delta(amount, unit)

    # -------------------------
    # X units from now
    # -------------------------
    match = re.fullmatch(r"(\d+) (day|week|month|year)s? from now", s)
    if match:
        amount = int(match.group(1))
        unit = match.group(2)
        return today + _make_delta(amount, unit)

    # -------------------------
    # Compound before/after:
    # "2 years, 3 months before Dec. 1, 2025"
    # "1 year and 2 months after yesterday"
    # -------------------------
    match = re.fullmatch(r"(.+?)\s+(before|after)\s+(.+)", s)
    if match:
        duration_str = match.group(1)
        direction = match.group(2)
        base_str = match.group(3)

        # parse base recursively
        base_date = parse(base_str, today)

        # split duration pieces
        parts = re.split(r"\s*(?:,|and)\s*", duration_str)

        delta = relativedelta()

        for part in parts:
            submatch = re.fullmatch(r"(\d+)\s*(day|week|month|year)s?", part)
            if not submatch:
                continue

            amount = int(submatch.group(1))
            unit = submatch.group(2)

            if unit == "day":
                delta += relativedelta(days=amount)
            elif unit == "week":
                delta += relativedelta(weeks=amount)
            elif unit == "month":
                delta += relativedelta(months=amount)
            elif unit == "year":
                delta += relativedelta(years=amount)

        # only return if at least one valid duration was found
        if delta != relativedelta():
            return base_date - delta if direction == "before" else base_date + delta

    # -------------------------
    # General relative:
    # "3 weeks before tomorrow"
    # -------------------------
    match = re.fullmatch(r"(\d+) (day|week|month|year)s? (before|after) (.+)", s)
    if match:
        amount = int(match.group(1))
        unit = match.group(2)
        direction = match.group(3)
        base_str = match.group(4)

        base_date = parse(base_str, today)
        delta = _make_delta(amount, unit)

        return base_date - delta if direction == "before" else base_date + delta

    # -------------------------
    # Fallback absolute parser
    # -------------------------
    try:
        return dt_parse(s).date()
    except Exception as e:
        raise ValueError(f"Could not parse date string: {s}") from e


def _make_delta(amount: int, unit: str):
    if unit == "day":
        return timedelta(days=amount)

    if unit == "week":
        return timedelta(weeks=amount)

    if unit == "month":
        return relativedelta(months=amount)

    if unit == "year":
        return relativedelta(years=amount)

    raise ValueError(f"Unsupported time unit: {unit}")


def _next_weekday(today: date, weekday_name: str) -> date:
    weekday_name = weekday_name.lower()

    if weekday_name not in WEEKDAYS:
        raise ValueError(f"Invalid weekday: {weekday_name}")

    target = WEEKDAYS[weekday_name]
    days_ahead = (target - today.weekday() + 7) % 7

    if days_ahead == 0:
        days_ahead = 7

    return today + timedelta(days=days_ahead)


def _last_weekday(today: date, weekday_name: str) -> date:
    weekday_name = weekday_name.lower()

    if weekday_name not in WEEKDAYS:
        raise ValueError(f"Invalid weekday: {weekday_name}")

    target = WEEKDAYS[weekday_name]
    days_behind = (today.weekday() - target + 7) % 7

    if days_behind == 0:
        days_behind = 7

    return today - timedelta(days=days_behind)
