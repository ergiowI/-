"""Фоновая задача: напоминание за N часов до записи и запрос оценки после визита."""
import asyncio
import logging
from datetime import datetime

from aiogram import Bot

from .config import Settings
from .db import Database
from .keyboards import rating_kb
from .texts import booking_card

log = logging.getLogger(__name__)


async def run_once(bot: Bot, settings: Settings, db: Database, now: datetime | None = None) -> None:
    """Один проход: напоминания перед визитом и запросы оценки после. Вынесено отдельно для тестов."""
    now = now or datetime.now(settings.tz)
    for b in db.due_reminders(now, settings.reminder_hours_before):
        db.mark_reminded(b.id)  # сначала помечаем, чтобы не слать дважды при сбое
        text = f"⏰ Напоминаем: вы записаны сегодня.\n\n{booking_card(b, settings, with_status=False)}\n📍 {settings.address}"
        try:
            await bot.send_message(b.chat_id, text)
        except Exception:
            log.warning("Не удалось отправить напоминание %s", b.id)
    for b in db.due_reviews(now, settings.review_hours_after):
        db.mark_review_asked(b.id)
        try:
            await bot.send_message(b.chat_id, "Как прошёл визит? Оцените, пожалуйста, нашу работу:", reply_markup=rating_kb(b.id))
        except Exception:
            log.warning("Не удалось запросить оценку %s", b.id)


async def reminder_loop(bot: Bot, settings: Settings, db: Database, interval: int = 60) -> None:
    while True:
        try:
            await run_once(bot, settings, db)
        except Exception:
            log.exception("Ошибка в цикле напоминаний")
        await asyncio.sleep(interval)
