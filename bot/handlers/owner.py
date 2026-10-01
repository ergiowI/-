"""Сторона владельца: уведомления, подтверждение/отмена, /today, /week."""
from datetime import datetime, time, timedelta

from aiogram import Bot, Router
from aiogram.filters import Command, Filter
from aiogram.types import CallbackQuery, Message

from .. import keyboards as kb
from ..config import Settings
from ..db import Booking, Database
from ..texts import booking_card, fmt_day

router = Router(name="owner")


class IsOwner(Filter):
    async def __call__(self, event: Message | CallbackQuery, settings: Settings) -> bool:
        return event.from_user.id == settings.owner_chat_id


router.message.filter(IsOwner())
router.callback_query.filter(IsOwner())


async def notify_owner(bot: Bot, settings: Settings, booking: Booking) -> None:
    await bot.send_message(
        settings.owner_chat_id,
        "🆕 Новая запись!\n\n" + booking_card(booking, settings, with_client=True),
        reply_markup=kb.owner_kb(booking.id),
    )


@router.callback_query(lambda c: c.data and c.data.startswith("own:"))
async def decide(cb: CallbackQuery, settings: Settings, db: Database):
    _, action, raw_id = cb.data.split(":")
    b = db.get(int(raw_id))
    if not b:
        return await cb.answer("Запись не найдена", show_alert=True)
    if b.status == "cancelled":
        return await cb.answer("Запись уже отменена", show_alert=True)
    if action == "ok":
        db.set_status(b.id, "confirmed")
        b.status = "confirmed"
        client_text = "✅ Ваша запись подтверждена!\n\n" + booking_card(b, settings) + f"\n📍 {settings.address}"
    else:
        db.set_status(b.id, "cancelled")
        b.status = "cancelled"
        client_text = f"😔 К сожалению, запись отменена. Позвоните нам: {settings.phone}\n\n" + booking_card(b, settings)
    await cb.message.edit_text(booking_card(b, settings, with_client=True), reply_markup=None)
    try:
        await cb.bot.send_message(b.chat_id, client_text)
    except Exception:  # клиент мог заблокировать бота
        pass
    await cb.answer("Готово")


async def _schedule(message: Message, settings: Settings, db: Database, days: int, title: str):
    today = datetime.now(settings.tz).date()
    start = datetime.combine(today, time.min, tzinfo=settings.tz)
    items = db.between(start, start + timedelta(days=days))
    if not items:
        return await message.answer(f"{title}: записей нет.")
    lines, current = [f"📆 {title}"], None
    for b in items:
        local = b.start.astimezone(settings.tz)
        if local.date() != current:
            current = local.date()
            lines.append(f"\n<b>{fmt_day(current)}</b>")
        svc = settings.services[b.service_id]
        mark = "✅" if b.status == "confirmed" else "⏳"
        lines.append(f"{mark} {local:%H:%M} — {svc.name}, {b.name}, {b.phone}")
    await message.answer("\n".join(lines), parse_mode="HTML")


@router.message(Command("today"))
async def today(message: Message, settings: Settings, db: Database):
    await _schedule(message, settings, db, 1, "Записи на сегодня")


@router.message(Command("week"))
async def week(message: Message, settings: Settings, db: Database):
    await _schedule(message, settings, db, 7, "Записи на неделю")
