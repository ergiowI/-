"""Чистая логика расчёта свободных слотов (без БД и Telegram, легко тестируется)."""
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

Interval = tuple[datetime, datetime]


def overlaps(a_start: datetime, a_end: datetime, b_start: datetime, b_end: datetime) -> bool:
    """Интервалы [start, end) пересекаются. Если один кончается там, где начинается другой, это не пересечение."""
    return a_start < b_end and b_start < a_end


def free_slots(
    day: date,
    duration_minutes: int,
    hours: tuple[time, time] | None,
    busy: list[Interval],
    now: datetime,
    tz: ZoneInfo,
    step_minutes: int = 30,
) -> list[datetime]:
    """Времена начала, на которые можно записаться в день `day`.

    hours  — (открытие, закрытие) или None для выходного;
    busy   — уже занятые интервалы (aware datetime);
    now    — текущее время (aware): прошедшие слоты сегодня отбрасываются.
    """
    if hours is None:
        return []
    open_dt = datetime.combine(day, hours[0], tzinfo=tz)
    close_dt = datetime.combine(day, hours[1], tzinfo=tz)
    duration = timedelta(minutes=duration_minutes)
    step = timedelta(minutes=step_minutes)

    result = []
    start = open_dt
    while start + duration <= close_dt:  # услуга должна закончиться до закрытия
        end = start + duration
        if start > now and not any(overlaps(start, end, b0, b1) for b0, b1 in busy):
            result.append(start)
        start += step
    return result


def bookable_days(today: date, days_ahead: int) -> list[date]:
    """Сегодня и ближайшие дни: всего `days_ahead` дат."""
    return [today + timedelta(days=i) for i in range(days_ahead)]
