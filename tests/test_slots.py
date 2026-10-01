"""Логика свободных слотов: пересечения, конец рабочего дня, прошедшее время сегодня."""
from zoneinfo import ZoneInfo

from bot.slots import bookable_days, free_slots, overlaps

from .helpers import DAY, EARLY, HOURS, TZ, dt, starts


def test_empty_day_full_grid():
    s = free_slots(DAY, 60, HOURS, [], EARLY, TZ, 60)
    assert starts(s) == ["09:00", "10:00", "11:00", "12:00", "13:00", "14:00", "15:00", "16:00", "17:00"]


def test_day_off():
    assert free_slots(DAY, 60, None, [], EARLY, TZ) == []


def test_service_must_end_before_closing():
    s = free_slots(DAY, 90, HOURS, [], EARLY, TZ, 30)
    assert starts(s)[-1] == "16:30"  # 16:30 + 1:30 = 18:00 ровно закрытие
    assert "17:00" not in starts(s)


def test_service_longer_than_day():
    assert free_slots(DAY, 600, HOURS, [], EARLY, TZ) == []


def test_busy_overlap_blocks_neighbours():
    # занято 11:00-12:00, услуга 60 мин: 10:30, 11:00, 11:30 пересекаются
    s = starts(free_slots(DAY, 60, HOURS, [(dt(11), dt(12))], EARLY, TZ, 30))
    assert "10:00" in s and "12:00" in s
    assert not {"10:30", "11:00", "11:30"} & set(s)


def test_touching_intervals_are_not_overlap():
    assert not overlaps(dt(10), dt(11), dt(11), dt(12))
    assert overlaps(dt(10), dt(11), dt(10, 59), dt(12))


def test_busy_spanning_whole_day():
    assert free_slots(DAY, 30, HOURS, [(dt(8), dt(19))], EARLY, TZ) == []


def test_past_time_today_is_hidden():
    now = dt(12, 10)
    s = starts(free_slots(DAY, 60, HOURS, [], now, TZ, 30))
    assert s[0] == "12:30"  # 12:00 уже прошло, 12:10 < 12:30


def test_slot_exactly_now_is_hidden():
    now = dt(12, 0)
    assert starts(free_slots(DAY, 30, HOURS, [], now, TZ, 30))[0] == "12:30"


def test_after_closing_today_nothing_left():
    assert free_slots(DAY, 30, HOURS, [], dt(17, 45), TZ) == []


def test_utc_busy_intervals_compare_correctly():
    busy = [(dt(11).astimezone(ZoneInfo("UTC")), dt(12).astimezone(ZoneInfo("UTC")))]
    assert "11:00" not in starts(free_slots(DAY, 60, HOURS, busy, EARLY, TZ, 30))


def test_bookable_days_are_consecutive():
    days = bookable_days(DAY, 7)
    assert len(days) == 7 and days[0] == DAY and (days[-1] - days[0]).days == 6


def test_step_grid_15_minutes():
    s = starts(free_slots(DAY, 30, HOURS, [], EARLY, TZ, 15))
    assert s[:3] == ["09:00", "09:15", "09:30"] and s[-1] == "17:30"
