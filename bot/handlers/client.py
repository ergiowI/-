"""Сценарий клиента: /start, запись, «Мои записи», «Контакты»."""
from datetime import date, datetime, time, timedelta

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from .. import keyboards as kb
from ..config import Settings
from ..db import Database
from ..slots import bookable_days, free_slots
from ..texts import booking_card, fmt_dt

router = Router(name="client")


class Booking(StatesGroup):
    service = State()
    day = State()
    time = State()
    name = State()
    phone = State()
    confirm = State()


def slots_for(db: Database, s: Settings, service_id: str, day: date) -> list[datetime]:
    """Свободные слоты на день с учётом БД. Единая точка, чтобы список и финальная проверка совпадали."""
    day_start = datetime.combine(day, time.min, tzinfo=s.tz)
    busy = db.busy_intervals(day_start, day_start + timedelta(days=1))
    return free_slots(
        day, s.services[service_id].duration_minutes, s.working_hours.get(day.weekday()),
        busy, datetime.now(s.tz), s.tz, s.slot_step_minutes,
    )


@router.message(CommandStart())
async def start(message: Message, state: FSMContext, settings: Settings):
    await state.clear()
    await message.answer(
        f"👋 Добро пожаловать в «{settings.business_name}»!\nЗапишитесь онлайн за минуту.",
        reply_markup=kb.main_menu(),
    )


@router.message(F.text == "📍 Контакты")
async def contacts(message: Message, settings: Settings):
    lines = [f"📍 {settings.address}", f"📞 {settings.phone}", "", "🕒 Часы работы:"]
    names = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    for i, n in enumerate(names):
        h = settings.working_hours.get(i)
        lines.append(f"{n}: {h[0]:%H:%M}–{h[1]:%H:%M}" if h else f"{n}: выходной")
    await message.answer("\n".join(lines))


@router.message(F.text == "📅 Записаться")
async def begin(message: Message, state: FSMContext, settings: Settings):
    await state.clear()
    await state.set_state(Booking.service)
    await message.answer("Выберите услугу:", reply_markup=kb.services_kb(settings))


@router.callback_query(Booking.service, F.data.startswith("svc:"))
async def pick_service(cb: CallbackQuery, state: FSMContext, settings: Settings, db: Database):
    service_id = cb.data.split(":")[1]
    if service_id not in settings.services:
        return await cb.answer("Неизвестная услуга")
    await state.update_data(service_id=service_id)
    today = datetime.now(settings.tz).date()
    days = [d for d in bookable_days(today, settings.booking_days_ahead) if slots_for(db, settings, service_id, d)]
    if not days:
        await cb.message.edit_text("😔 На ближайшие дни свободного времени нет. Позвоните нам: " + settings.phone)
        await state.clear()
        return await cb.answer()
    await state.set_state(Booking.day)
    await cb.message.edit_text("Выберите дату:", reply_markup=kb.days_kb(days))
    await cb.answer()


@router.callback_query(F.data == "back:svc")
async def back_service(cb: CallbackQuery, state: FSMContext, settings: Settings):
    await state.set_state(Booking.service)
    await cb.message.edit_text("Выберите услугу:", reply_markup=kb.services_kb(settings))
    await cb.answer()


@router.callback_query(Booking.day, F.data.startswith("day:"))
@router.callback_query(Booking.time, F.data == "back:day")
async def pick_day(cb: CallbackQuery, state: FSMContext, settings: Settings, db: Database):
    data = await state.get_data()
    if cb.data.startswith("day:"):
        day = date.fromisoformat(cb.data.split(":", 1)[1])
        await state.update_data(day=day.isoformat())
    else:
        day = date.fromisoformat(data["day"])
    slots = slots_for(db, settings, data["service_id"], day)
    if not slots:
        return await cb.answer("На эту дату времени уже нет", show_alert=True)
    await state.set_state(Booking.time)
    await cb.message.edit_text("Выберите время:", reply_markup=kb.times_kb(slots))
    await cb.answer()


@router.callback_query(Booking.time, F.data.startswith("time:"))
async def pick_time(cb: CallbackQuery, state: FSMContext):
    hhmm = cb.data.split(":")[1]
    await state.update_data(time=hhmm)
    await state.set_state(Booking.name)
    await cb.message.edit_text("Как вас зовут?")
    await cb.answer()


@router.message(Booking.name, F.text)
async def get_name(message: Message, state: FSMContext):
    name = message.text.strip()[:60]
    if len(name) < 2:
        return await message.answer("Введите имя (минимум 2 символа)")
    await state.update_data(name=name)
    await state.set_state(Booking.phone)
    await message.answer("Поделитесь номером телефона кнопкой ниже (или напишите его):", reply_markup=kb.phone_kb())


def _summary(data: dict, s: Settings) -> tuple[str, datetime, datetime]:
    service = s.services[data["service_id"]]
    start = datetime.combine(date.fromisoformat(data["day"]), time(int(data["time"][:2]), int(data["time"][2:])), tzinfo=s.tz)
    end = start + timedelta(minutes=service.duration_minutes)
    text = (
        "Проверьте запись:\n\n"
        f"🔧 {service.name} — {service.price} ₽\n🕒 {fmt_dt(start)} ({service.duration_minutes} мин)\n"
        f"👤 {data['name']}\n📞 {data['phone']}\n📍 {s.address}"
    )
    return text, start, end


@router.message(Booking.phone, F.contact | F.text)
async def get_phone(message: Message, state: FSMContext, settings: Settings):
    phone = message.contact.phone_number if message.contact else message.text.strip()
    digits = "".join(ch for ch in phone if ch.isdigit())
    if not 10 <= len(digits) <= 15:
        return await message.answer("Не похоже на номер телефона. Попробуйте ещё раз или нажмите кнопку.")
    if message.contact and not phone.startswith("+"):
        phone = "+" + digits  # Telegram иногда отдаёт номер без «+»
    await state.update_data(phone=phone)
    await state.set_state(Booking.confirm)
    text, _, _ = _summary(await state.get_data(), settings)
    await message.answer("Спасибо!", reply_markup=kb.main_menu())
    await message.answer(text, reply_markup=kb.confirm_kb())


@router.callback_query(Booking.confirm, F.data == "confirm:no")
async def confirm_no(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    await cb.message.edit_text("Запись отменена. Начать заново: «📅 Записаться»")
    await cb.answer()


@router.callback_query(Booking.confirm, F.data == "confirm:yes")
async def confirm_yes(cb: CallbackQuery, state: FSMContext, settings: Settings, db: Database):
    from .owner import notify_owner

    data = await state.get_data()
    _, start, end = _summary(data, settings)
    if start <= datetime.now(settings.tz):
        await state.clear()
        await cb.message.edit_text("Это время уже прошло. Начните запись заново.")
        return await cb.answer()
    booking = db.create_booking(cb.from_user.id, data["name"], data["phone"], data["service_id"], start, end)
    if booking is None:  # кто-то успел раньше
        await state.set_state(Booking.day)
        today = datetime.now(settings.tz).date()
        days = [d for d in bookable_days(today, settings.booking_days_ahead) if slots_for(db, settings, data["service_id"], d)]
        await cb.message.edit_text("😔 Это время только что заняли. Выберите другое:", reply_markup=kb.days_kb(days))
        return await cb.answer()
    await state.clear()
    await cb.message.edit_text(
        "✅ Заявка отправлена! Мы подтвердим запись в ближайшее время.\n\n" + booking_card(booking, settings)
    )
    await notify_owner(cb.bot, settings, booking)
    await cb.answer()


@router.message(F.text == "📋 Мои записи")
async def my_bookings(message: Message, settings: Settings, db: Database):
    items = db.user_upcoming(message.chat.id, datetime.now(settings.tz))
    if not items:
        return await message.answer("У вас нет будущих записей.")
    for b in items:
        await message.answer(booking_card(b, settings), reply_markup=kb.my_booking_kb(b.id))


@router.callback_query(F.data.startswith("cancel:"))
async def cancel_booking(cb: CallbackQuery, settings: Settings, db: Database):
    b = db.get(int(cb.data.split(":")[1]))
    if not b or b.chat_id != cb.from_user.id or b.status == "cancelled":
        return await cb.answer("Запись не найдена", show_alert=True)
    db.set_status(b.id, "cancelled")
    b.status = "cancelled"
    await cb.message.edit_text(booking_card(b, settings))
    await cb.bot.send_message(settings.owner_chat_id, "❗ Клиент отменил запись:\n\n" + booking_card(b, settings, with_client=True))
    await cb.answer("Запись отменена")
