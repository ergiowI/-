"""Сторона владельца: уведомления, подтверждение/отмена, /today, /week, /stats, /broadcast, /export, /help."""
import asyncio
import csv
import io
from datetime import datetime, time, timedelta

from aiogram import Bot, Router
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import Command, CommandObject, Filter
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, CallbackQuery, Message

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


async def notify_owner(bot: Bot, settings: Settings, booking: Booking, title: str = "🆕 Новая запись!") -> None:
    await bot.send_message(
        settings.owner_chat_id,
        f"{title}\n\n" + booking_card(booking, settings, with_client=True),
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


@router.message(Command("stats"))
async def stats(message: Message, settings: Settings, db: Database):
    """Сводка: прошедшие 7 дней (факт) и следующие 7 дней (загрузка)."""
    now = datetime.now(settings.tz)
    today = datetime.combine(now.date(), time.min, tzinfo=settings.tz)
    past = db.all_between(today - timedelta(days=7), today)
    future = db.all_between(today, today + timedelta(days=7))

    done = [b for b in past if b.status == "confirmed"]
    cancelled = [b for b in past if b.status == "cancelled"]
    revenue = sum(settings.services[b.service_id].price for b in done)
    ratings = [b.rating for b in past if b.rating]
    upcoming = [b for b in future if b.status != "cancelled"]
    pending = [b for b in upcoming if b.status == "pending"]

    popular: dict[str, int] = {}
    for b in done + upcoming:
        popular[b.service_id] = popular.get(b.service_id, 0) + 1
    top = max(popular, key=popular.get) if popular else None

    lines = [
        "📊 <b>Статистика</b>",
        "",
        "<b>Прошедшие 7 дней</b>",
        f"Визитов: {len(done)} · отмен: {len(cancelled)}",
        f"Выручка по прайсу: {revenue:,} ₽".replace(",", " "),
        f"Средняя оценка: {sum(ratings) / len(ratings):.1f} ⭐ ({len(ratings)} шт.)" if ratings else "Оценок пока нет",
        "",
        "<b>Следующие 7 дней</b>",
        f"Записей: {len(upcoming)} · ждут подтверждения: {len(pending)}",
    ]
    if top:
        lines.append(f"Популярная услуга: {settings.services[top].name}")
    await message.answer("\n".join(lines), parse_mode="HTML")


@router.message(Command("help"))
async def owner_help(message: Message):
    await message.answer(
        "Команды владельца:\n"
        "/today — записи на сегодня\n"
        "/week — записи на 7 дней\n"
        "/stats — статистика и загрузка\n"
        "/broadcast текст — рассылка всем клиентам (сначала покажу предпросмотр)\n"
        "/export — все записи в CSV для Excel / Google Таблиц\n\n"
        "Новые записи и переносы приходят сюда с кнопками «Подтвердить» / «Отменить»."
    )


# ===== Рассылка =====
@router.message(Command("broadcast"))
async def broadcast_preview(message: Message, command: CommandObject, state: FSMContext, db: Database, settings: Settings):
    text = (command.args or "").strip()
    if not text:
        return await message.answer(
            "Напишите текст после команды, например:\n"
            "/broadcast Скоро снег! Есть свободные окна на переобувку во вторник и среду."
        )
    recipients = [c for c in db.subscribers() if c != settings.owner_chat_id]
    if not recipients:
        return await message.answer("Пока некому отправлять: клиенты появятся после первых записей.")
    await state.update_data(broadcast=text)
    await message.answer(f"Предпросмотр рассылки:\n\n{text}", reply_markup=kb.broadcast_kb(len(recipients)))


@router.callback_query(lambda c: c.data in ("bc:send", "bc:cancel"))
async def broadcast_send(cb: CallbackQuery, state: FSMContext, db: Database, settings: Settings):
    text = (await state.get_data()).get("broadcast")
    await state.update_data(broadcast=None)
    if cb.data == "bc:cancel" or not text:
        await cb.message.edit_text("Рассылка отменена." if text else "Рассылка уже отправлена или устарела.")
        return await cb.answer()
    await cb.message.edit_text(f"Отправляю…\n\n{text}")
    await cb.answer()
    sent = failed = 0
    for chat_id in db.subscribers():
        if chat_id == settings.owner_chat_id:
            continue
        try:
            await cb.bot.send_message(chat_id, text, reply_markup=kb.unsubscribe_kb())
            sent += 1
        except TelegramAPIError:  # клиент заблокировал бота или удалил аккаунт
            failed += 1
        await asyncio.sleep(0.05)  # не больше ~20 сообщений в секунду — лимит Telegram
    report = f"✅ Рассылка отправлена: {sent}"
    if failed:
        report += f"\nНе доставлено: {failed} (заблокировали бота)"
    await cb.message.edit_text(f"{report}\n\n{text}")


# ===== Выгрузка =====
@router.message(Command("export"))
async def export_csv(message: Message, settings: Settings, db: Database):
    """Все записи за последние 90 дней и будущие — CSV (разделитель «;», открывается в Excel и Google Таблицах)."""
    now = datetime.now(settings.tz)
    items = db.all_between(now - timedelta(days=90), now + timedelta(days=365))
    if not items:
        return await message.answer("Записей пока нет — выгружать нечего.")
    buf = io.StringIO()
    w = csv.writer(buf, delimiter=";")
    w.writerow(["№", "Дата", "Время", "Услуга", "Цена, ₽", "Клиент", "Телефон", "Комментарий", "Статус", "Оценка"])
    status = {"pending": "ожидает", "confirmed": "подтверждена", "cancelled": "отменена"}
    for b in items:
        start = b.start.astimezone(settings.tz)
        svc = settings.services.get(b.service_id)
        w.writerow([b.id, start.strftime("%d.%m.%Y"), start.strftime("%H:%M"), svc.name if svc else b.service_id,
                    svc.price if svc else "", b.name, b.phone, b.comment, status.get(b.status, b.status), b.rating or ""])
    data = buf.getvalue().encode("utf-8-sig")  # BOM — чтобы Excel правильно показал русские буквы
    name = f"zapisi_{now:%Y-%m-%d}.csv"
    await message.answer_document(BufferedInputFile(data, filename=name), caption=f"📄 Записей: {len(items)} (90 дней назад и все будущие)")
