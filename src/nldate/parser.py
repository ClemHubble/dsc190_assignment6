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


def parse(s: str, today: date | None = None) -> date:
    """
    Parse natural language date expressions into datetime.date objects.
    """
    if today is None:
        today = date.today()

    s = s.strip().lower()
    s = re.sub(r"\b(a|an)\b", "1", s)

    # Simple keywords
    if s == "today":
        return today
    if s == "tomorrow":
        return today + timedelta(days=1)
    if s == "yesterday":
        return today - timedelta(days=1)

    # next weekday
    match = re.fullmatch(r"next (\w+)", s)
    if match:
        return _next_weekday(today, match.group(1))

    # last weekday
    match = re.fullmatch(r"last (\w+)", s)
    if match:
        return _last_weekday(today, match.group(1))

    # in X days/weeks/months/years
    match = re.fullmatch(r"in (\d+) (day|week|month|year)s?", s)
    if match:
        amount = int(match.group(1))
        unit = match.group(2)
        return today + _make_delta(amount, unit)

    # X days/weeks/months/years ago
    match = re.fullmatch(r"(\d+) (day|week|month|year)s? ago", s)
    if match:
        amount = int(match.group(1))
        unit = match.group(2)
        return today - _make_delta(amount, unit)

    # Compound: X years and Y months after/before ...
    match = re.fullmatch(r"(\d+) years? and (\d+) months? (before|after) (.+)", s)
    if match:
        years = int(match.group(1))
        months = int(match.group(2))
        direction = match.group(3)
        base = parse(match.group(4), today)

        delta = relativedelta(years=years, months=months)

        return base - delta if direction == "before" else base + delta

    # General relative: X unit before/after DATE
    match = re.fullmatch(r"(\d+) (day|week|month|year)s? (before|after) (.+)", s)
    if match:
        amount = int(match.group(1))
        unit = match.group(2)
        direction = match.group(3)
        base_str = match.group(4)

        base_date = parse(base_str, today)
        delta = _make_delta(amount, unit)

        return base_date - delta if direction == "before" else base_date + delta

    # Fallback: absolute date parsing
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
