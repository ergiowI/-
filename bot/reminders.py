"""Фоновая задача: напоминание клиенту за N часов до подтверждённой записи."""
import asyncio
import logging
from datetime import datetime

from aiogram import Bot

from .config import Settings
from .db import Database
from .texts import booking_card

log = logging.getLogger(__name__)


async def reminder_loop(bot: Bot, settings: Settings, db: Database, interval: int = 60) -> None:
    while True:
        try:
            for b in db.due_reminders(datetime.now(settings.tz), settings.reminder_hours_before):
                db.mark_reminded(b.id)  # сначала помечаем, чтобы не слать дважды при сбое
                text = f"⏰ Напоминаем: вы записаны сегодня.\n\n{booking_card(b, settings, with_status=False)}\n📍 {settings.address}"
                try:
                    await bot.send_message(b.chat_id, text)
                except Exception:
                    log.warning("Не удалось отправить напоминание %s", b.id)
        except Exception:
            log.exception("Ошибка в цикле напоминаний")
        await asyncio.sleep(interval)
