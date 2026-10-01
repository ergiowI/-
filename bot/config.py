"""Загрузка настроек: бизнес-данные из config.yaml, секреты из .env."""
import os
from dataclasses import dataclass
from datetime import time
from pathlib import Path
from zoneinfo import ZoneInfo

import yaml
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Service:
    id: str
    name: str
    duration_minutes: int
    price: int


@dataclass(frozen=True)
class Settings:
    bot_token: str
    owner_chat_id: int
    business_name: str
    address: str
    phone: str
    tz: ZoneInfo
    working_hours: dict[int, tuple[time, time]]
    slot_step_minutes: int
    reminder_hours_before: int
    booking_days_ahead: int
    services: dict[str, Service]
    db_path: Path


def _parse_time(value: str) -> time:
    hours, minutes = value.split(":")
    return time(int(hours), int(minutes))


def load_settings(config_path: Path | None = None) -> Settings:
    load_dotenv(ROOT / ".env")
    token = os.getenv("BOT_TOKEN", "").strip()
    owner = os.getenv("OWNER_CHAT_ID", "").strip()
    if not token or not owner:
        raise RuntimeError("Заполните BOT_TOKEN и OWNER_CHAT_ID в файле .env")

    raw = yaml.safe_load((config_path or ROOT / "config.yaml").read_text(encoding="utf-8"))
    business = raw["business"]
    services = {
        s["id"]: Service(s["id"], s["name"], int(s["duration_minutes"]), int(s["price"]))
        for s in raw["services"]
    }
    hours = {
        int(day): (_parse_time(start), _parse_time(end))
        for day, (start, end) in raw["working_hours"].items()
    }
    return Settings(
        bot_token=token,
        owner_chat_id=int(owner),
        business_name=business["name"],
        address=business["address"],
        phone=business["phone"],
        tz=ZoneInfo(raw.get("timezone", "Europe/Moscow")),
        working_hours=hours,
        slot_step_minutes=int(raw.get("slot_step_minutes", 30)),
        reminder_hours_before=int(raw.get("reminder_hours_before", 2)),
        booking_days_ahead=int(raw.get("booking_days_ahead", 7)),
        services=services,
        db_path=ROOT / "bookings.db",
    )
