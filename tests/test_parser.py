from datetime import date
from nldate import parse


def test_absolute_date():
    assert parse("December 1st, 2025") == date(2025, 12, 1)


def test_next_tuesday():
    assert parse("next Tuesday", today=date(2025, 5, 7)) == date(2025, 5, 13)


def test_yesterday():
    assert parse("yesterday", today=date(2025, 5, 10)) == date(2025, 5, 9)


def test_tomorrow():
    assert parse("tomorrow", today=date(2025, 5, 10)) == date(2025, 5, 11)


def test_in_days():
    assert parse("in 5 days", today=date(2025, 5, 10)) == date(2025, 5, 15)


def test_days_before():
    assert parse("5 days before December 1st, 2025") == date(2025, 11, 26)


def test_weeks_after():
    assert parse("2 weeks after January 1st, 2025") == date(2025, 1, 15)


def test_months_after():
    assert parse("1 month after January 15th, 2025") == date(2025, 2, 15)


def test_years_after():
    assert parse("1 year after January 1st, 2025") == date(2026, 1, 1)


def test_compound_relative():
    assert parse(
        "1 year and 2 months after yesterday", today=date(2025, 5, 10)
    ) == date(2026, 7, 9)


def test_last_weekday():
    assert parse("last Monday", today=date(2025, 5, 10)) == date(2025, 5, 5)


def test_next_monday():
    assert parse("next Monday", today=date(2025, 5, 10)) == date(2025, 5, 12)


def test_ago_days():
    assert parse("3 days ago", today=date(2025, 5, 10)) == date(2025, 5, 7)


def test_case_insensitivity():
    assert parse("ToMoRrOw", today=date(2025, 5, 10)) == date(2025, 5, 11)


def test_in_weeks():
    assert parse("in 2 weeks", today=date(2025, 5, 10)) == date(2025, 5, 24)
