"""SQLite: записи и клиенты. Двойная запись исключается проверкой пересечения внутри BEGIN IMMEDIATE."""
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

ACTIVE = ("pending", "confirmed")  # статусы, которые занимают время

SCHEMA = """
CREATE TABLE IF NOT EXISTS bookings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    phone TEXT NOT NULL,
    service_id TEXT NOT NULL,
    start_ts INTEGER NOT NULL,      -- unix time, UTC
    end_ts INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',   -- pending | confirmed | cancelled
    reminded INTEGER NOT NULL DEFAULT 0,
    comment TEXT NOT NULL DEFAULT '',          -- комментарий клиента (марка авто, порода питомца...)
    review_asked INTEGER NOT NULL DEFAULT 0,
    rating INTEGER                             -- оценка 1..5 после визита
);
CREATE INDEX IF NOT EXISTS idx_bookings_start ON bookings(start_ts);
CREATE TABLE IF NOT EXISTS clients (           -- запоминаем имя и телефон для повторных записей
    chat_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    phone TEXT NOT NULL
);
"""


@dataclass
class Booking:
    id: int
    chat_id: int
    name: str
    phone: str
    service_id: str
    start_ts: int
    end_ts: int
    status: str
    reminded: int
    comment: str = ""
    review_asked: int = 0
    rating: int | None = None

    @property
    def start(self) -> datetime:
        return datetime.fromtimestamp(self.start_ts, timezone.utc)

    @property
    def end(self) -> datetime:
        return datetime.fromtimestamp(self.end_ts, timezone.utc)


def _ts(dt: datetime) -> int:
    return int(dt.timestamp())


class Database:
    def __init__(self, path: Path | str):
        self.path = str(path)
        with self._conn() as c:
            c.executescript(SCHEMA)
            # миграция для баз, созданных старой версией бота
            cols = {r["name"] for r in c.execute("PRAGMA table_info(bookings)")}
            for name, ddl in [("comment", "TEXT NOT NULL DEFAULT ''"), ("review_asked", "INTEGER NOT NULL DEFAULT 0"), ("rating", "INTEGER")]:
                if name not in cols:
                    c.execute(f"ALTER TABLE bookings ADD COLUMN {name} {ddl}")

    @contextmanager
    def _conn(self):
        conn = sqlite3.connect(self.path, timeout=10, isolation_level=None)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    @staticmethod
    def _row(row) -> Booking:
        return Booking(**dict(row))

    @staticmethod
    def _clash(c, start: datetime, end: datetime, exclude_id: int = 0) -> bool:
        return c.execute(
            "SELECT 1 FROM bookings WHERE status IN (?, ?) AND start_ts < ? AND end_ts > ? AND id != ? LIMIT 1",
            (*ACTIVE, _ts(end), _ts(start), exclude_id),
        ).fetchone() is not None

    def create_booking(self, chat_id, name, phone, service_id, start: datetime, end: datetime, comment: str = "") -> Booking | None:
        """Создаёт запись или возвращает None, если время уже занято."""
        with self._conn() as c:
            c.execute("BEGIN IMMEDIATE")  # блокируем запись: проверка + вставка атомарны
            try:
                if self._clash(c, start, end):
                    c.execute("ROLLBACK")
                    return None
                cur = c.execute(
                    "INSERT INTO bookings (chat_id, name, phone, service_id, start_ts, end_ts, comment) VALUES (?,?,?,?,?,?,?)",
                    (chat_id, name, phone, service_id, _ts(start), _ts(end), comment),
                )
                c.execute("COMMIT")
                return self.get(cur.lastrowid)
            except Exception:
                c.execute("ROLLBACK")
                raise

    def reschedule(self, booking_id: int, start: datetime, end: datetime) -> bool:
        """Переносит запись на новое время (саму себя при проверке не учитываем). Снова ждёт подтверждения."""
        with self._conn() as c:
            c.execute("BEGIN IMMEDIATE")
            try:
                if self._clash(c, start, end, exclude_id=booking_id):
                    c.execute("ROLLBACK")
                    return False
                c.execute(
                    "UPDATE bookings SET start_ts=?, end_ts=?, status='pending', reminded=0 WHERE id=?",
                    (_ts(start), _ts(end), booking_id),
                )
                c.execute("COMMIT")
                return True
            except Exception:
                c.execute("ROLLBACK")
                raise

    def get(self, booking_id: int) -> Booking | None:
        with self._conn() as c:
            row = c.execute("SELECT * FROM bookings WHERE id=?", (booking_id,)).fetchone()
        return self._row(row) if row else None

    def busy_intervals(self, day_start: datetime, day_end: datetime) -> list[tuple[datetime, datetime]]:
        with self._conn() as c:
            rows = c.execute(
                "SELECT start_ts, end_ts FROM bookings WHERE status IN (?, ?) AND start_ts < ? AND end_ts > ?",
                (*ACTIVE, _ts(day_end), _ts(day_start)),
            ).fetchall()
        return [
            (datetime.fromtimestamp(r["start_ts"], timezone.utc), datetime.fromtimestamp(r["end_ts"], timezone.utc))
            for r in rows
        ]

    def set_status(self, booking_id: int, status: str) -> None:
        with self._conn() as c:
            c.execute("UPDATE bookings SET status=? WHERE id=?", (status, booking_id))

    def user_upcoming(self, chat_id: int, now: datetime) -> list[Booking]:
        with self._conn() as c:
            rows = c.execute(
                "SELECT * FROM bookings WHERE chat_id=? AND status IN (?, ?) AND start_ts > ? ORDER BY start_ts",
                (chat_id, *ACTIVE, _ts(now)),
            ).fetchall()
        return [self._row(r) for r in rows]

    def between(self, start: datetime, end: datetime) -> list[Booking]:
        with self._conn() as c:
            rows = c.execute(
                "SELECT * FROM bookings WHERE status IN (?, ?) AND start_ts >= ? AND start_ts < ? ORDER BY start_ts",
                (*ACTIVE, _ts(start), _ts(end)),
            ).fetchall()
        return [self._row(r) for r in rows]

    def due_reminders(self, now: datetime, hours_before: int) -> list[Booking]:
        limit = _ts(now) + hours_before * 3600
        with self._conn() as c:
            rows = c.execute(
                "SELECT * FROM bookings WHERE status='confirmed' AND reminded=0 AND start_ts > ? AND start_ts <= ?",
                (_ts(now), limit),
            ).fetchall()
        return [self._row(r) for r in rows]

    def mark_reminded(self, booking_id: int) -> None:
        with self._conn() as c:
            c.execute("UPDATE bookings SET reminded=1 WHERE id=?", (booking_id,))

    def due_reviews(self, now: datetime, hours_after: int) -> list[Booking]:
        """Подтверждённые визиты, закончившиеся hours_after часов назад (но не раньше суток), без запроса оценки."""
        edge = _ts(now) - hours_after * 3600
        with self._conn() as c:
            rows = c.execute(
                "SELECT * FROM bookings WHERE status='confirmed' AND review_asked=0 AND end_ts <= ? AND end_ts > ?",
                (edge, edge - 24 * 3600),
            ).fetchall()
        return [self._row(r) for r in rows]

    def mark_review_asked(self, booking_id: int) -> None:
        with self._conn() as c:
            c.execute("UPDATE bookings SET review_asked=1 WHERE id=?", (booking_id,))

    def set_rating(self, booking_id: int, rating: int) -> None:
        with self._conn() as c:
            c.execute("UPDATE bookings SET rating=? WHERE id=?", (rating, booking_id))

    def all_between(self, start: datetime, end: datetime) -> list[Booking]:
        """Все записи периода, включая отменённые (для статистики)."""
        with self._conn() as c:
            rows = c.execute(
                "SELECT * FROM bookings WHERE start_ts >= ? AND start_ts < ? ORDER BY start_ts", (_ts(start), _ts(end))
            ).fetchall()
        return [self._row(r) for r in rows]

    def get_client(self, chat_id: int) -> tuple[str, str] | None:
        with self._conn() as c:
            row = c.execute("SELECT name, phone FROM clients WHERE chat_id=?", (chat_id,)).fetchone()
        return (row["name"], row["phone"]) if row else None

    def save_client(self, chat_id: int, name: str, phone: str) -> None:
        with self._conn() as c:
            c.execute(
                "INSERT INTO clients (chat_id, name, phone) VALUES (?,?,?) "
                "ON CONFLICT(chat_id) DO UPDATE SET name=excluded.name, phone=excluded.phone",
                (chat_id, name, phone),
            )
