"""Общие данные для тестов: фиксированный день и часовой пояс."""
from datetime import date, datetime, time
from zoneinfo import ZoneInfo

TZ = ZoneInfo("Europe/Moscow")
DAY = date(2030, 1, 14)  # понедельник
HOURS = (time(9, 0), time(18, 0))
EARLY = datetime(2030, 1, 1, 0, 0, tzinfo=TZ)  # «сейчас» гораздо раньше дня


def dt(h, m=0):
    return datetime.combine(DAY, time(h, m), tzinfo=TZ)


def starts(slots):
    return [s.strftime("%H:%M") for s in slots]
