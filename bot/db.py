"""SQLite: записи. Двойная запись исключается проверкой пересечения внутри BEGIN IMMEDIATE."""
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
    reminded INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_bookings_start ON bookings(start_ts);
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

    def create_booking(self, chat_id, name, phone, service_id, start: datetime, end: datetime) -> Booking | None:
        """Создаёт запись или возвращает None, если время уже занято."""
        with self._conn() as c:
            c.execute("BEGIN IMMEDIATE")  # блокируем запись: проверка + вставка атомарны
            try:
                clash = c.execute(
                    "SELECT 1 FROM bookings WHERE status IN (?, ?) AND start_ts < ? AND end_ts > ? LIMIT 1",
                    (*ACTIVE, _ts(end), _ts(start)),
                ).fetchone()
                if clash:
                    c.execute("ROLLBACK")
                    return None
                cur = c.execute(
                    "INSERT INTO bookings (chat_id, name, phone, service_id, start_ts, end_ts) VALUES (?,?,?,?,?,?)",
                    (chat_id, name, phone, service_id, _ts(start), _ts(end)),
                )
                c.execute("COMMIT")
                return self.get(cur.lastrowid)
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
