from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from bot.db import Database
from bot.slots import free_slots, overlaps

TZ = ZoneInfo("Europe/Moscow")
DAY = date(2030, 1, 14)  # понедельник
HOURS = (time(9, 0), time(18, 0))
EARLY = datetime(2030, 1, 1, 0, 0, tzinfo=TZ)  # «сейчас» гораздо раньше дня


def dt(h, m=0):
    return datetime.combine(DAY, time(h, m), tzinfo=TZ)


def starts(slots):
    return [s.strftime("%H:%M") for s in slots]


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


def test_db_rejects_double_booking(tmp_path):
    db = Database(tmp_path / "t.db")
    first = db.create_booking(1, "А", "+7", "x", dt(11), dt(12))
    assert first is not None
    assert db.create_booking(2, "Б", "+7", "x", dt(11, 30), dt(12, 30)) is None  # пересечение
    assert db.create_booking(2, "Б", "+7", "x", dt(12), dt(13)) is not None  # встык, ок


def test_db_cancelled_frees_slot(tmp_path):
    db = Database(tmp_path / "t.db")
    b = db.create_booking(1, "А", "+7", "x", dt(11), dt(12))
    db.set_status(b.id, "cancelled")
    assert db.create_booking(2, "Б", "+7", "x", dt(11), dt(12)) is not None


def test_reminders_window(tmp_path):
    db = Database(tmp_path / "t.db")
    now = dt(10)
    near = db.create_booking(1, "А", "+7", "x", now + timedelta(hours=1), now + timedelta(hours=2))
    far = db.create_booking(1, "А", "+7", "x", now + timedelta(hours=5), now + timedelta(hours=6))
    db.set_status(near.id, "confirmed")
    db.set_status(far.id, "confirmed")
    due = db.due_reminders(now, 2)
    assert [b.id for b in due] == [near.id]
    db.mark_reminded(near.id)
    assert db.due_reminders(now, 2) == []
