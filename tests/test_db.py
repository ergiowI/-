"""SQLite: защита от двойной записи, перенос, клиенты, напоминания, оценки, миграция."""
import sqlite3
from datetime import timedelta

from bot.db import Database

from .helpers import dt


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


def test_db_reschedule_ignores_itself_and_checks_others(tmp_path):
    db = Database(tmp_path / "t.db")
    a = db.create_booking(1, "А", "+7", "x", dt(11), dt(12))
    db.create_booking(2, "Б", "+7", "x", dt(13), dt(14))
    db.set_status(a.id, "confirmed")
    assert db.reschedule(a.id, dt(11, 30), dt(12, 30))  # пересекается только сама с собой — можно
    moved = db.get(a.id)
    assert moved.status == "pending" and moved.reminded == 0  # перенос снова ждёт подтверждения
    assert not db.reschedule(a.id, dt(13, 30), dt(14, 30))  # занято другим клиентом


def test_clients_are_remembered(tmp_path):
    db = Database(tmp_path / "t.db")
    assert db.get_client(1) is None
    db.save_client(1, "Иван", "+7 999")
    db.save_client(1, "Иван П.", "+7 888")
    assert db.get_client(1) == ("Иван П.", "+7 888")


def test_review_requested_after_visit_once(tmp_path):
    db = Database(tmp_path / "t.db")
    b = db.create_booking(1, "А", "+7", "x", dt(10), dt(11), comment="Kia Rio R15")
    db.set_status(b.id, "confirmed")
    assert db.due_reviews(dt(11, 30), 1) == []  # прошло меньше часа
    assert [x.id for x in db.due_reviews(dt(12, 5), 1)] == [b.id]
    db.mark_review_asked(b.id)
    assert db.due_reviews(dt(12, 5), 1) == []
    assert db.get(b.id).comment == "Kia Rio R15"


def test_migration_adds_new_columns(tmp_path):
    path = tmp_path / "old.db"
    con = sqlite3.connect(path)
    con.execute("CREATE TABLE bookings (id INTEGER PRIMARY KEY AUTOINCREMENT, chat_id INTEGER NOT NULL, name TEXT NOT NULL, phone TEXT NOT NULL, service_id TEXT NOT NULL, start_ts INTEGER NOT NULL, end_ts INTEGER NOT NULL, status TEXT NOT NULL DEFAULT 'pending', reminded INTEGER NOT NULL DEFAULT 0)")
    con.commit(); con.close()
    db = Database(path)
    assert db.create_booking(1, "А", "+7", "x", dt(10), dt(11), comment="ok").comment == "ok"


def test_cancelled_booking_not_reminded(tmp_path):
    db = Database(tmp_path / "t.db")
    now = dt(10)
    b = db.create_booking(1, "А", "+7", "x", now + timedelta(hours=1), now + timedelta(hours=2))
    assert db.due_reminders(now, 2) == []  # pending — не напоминаем
    db.set_status(b.id, "cancelled")
    assert db.due_reminders(now, 2) == []


def test_user_upcoming_only_own_future_active(tmp_path):
    db = Database(tmp_path / "t.db")
    past = db.create_booking(1, "А", "+7", "x", dt(9), dt(10))
    mine = db.create_booking(1, "А", "+7", "x", dt(12), dt(13))
    db.create_booking(2, "Б", "+7", "x", dt(14), dt(15))
    cancelled = db.create_booking(1, "А", "+7", "x", dt(16), dt(17))
    db.set_status(cancelled.id, "cancelled")
    assert [b.id for b in db.user_upcoming(1, dt(11))] == [mine.id]
    assert past.id != mine.id


def test_all_between_includes_cancelled(tmp_path):
    db = Database(tmp_path / "t.db")
    b = db.create_booking(1, "А", "+7", "x", dt(10), dt(11))
    db.set_status(b.id, "cancelled")
    assert len(db.between(dt(0), dt(23))) == 0
    assert len(db.all_between(dt(0), dt(23))) == 1
