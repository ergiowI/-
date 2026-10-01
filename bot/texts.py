"""Форматирование дат и карточек записей."""
from datetime import datetime

from .config import Service, Settings
from .db import Booking

WEEKDAYS = ["пн", "вт", "ср", "чт", "пт", "сб", "вс"]
STATUS = {"pending": "⏳ ожидает подтверждения", "confirmed": "✅ подтверждена", "cancelled": "❌ отменена"}


def fmt_day(d) -> str:
    return f"{d.strftime('%d.%m')} ({WEEKDAYS[d.weekday()]})"


def fmt_dt(dt: datetime) -> str:
    return f"{fmt_day(dt)} {dt.strftime('%H:%M')}"


def booking_card(b: Booking, s: Settings, with_client: bool = False, with_status: bool = True) -> str:
    service: Service = s.services[b.service_id]
    start = b.start.astimezone(s.tz)
    lines = [
        f"🔧 {service.name} — {service.price} ₽",
        f"🕒 {fmt_dt(start)} ({service.duration_minutes} мин)",
    ]
    if with_client:
        lines += [f"👤 {b.name}", f"📞 {b.phone}"]
    if with_status:
        lines.append(f"Статус: {STATUS[b.status]}")
    return "\n".join(lines)
