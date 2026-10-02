"""Сценарий клиента: /start, запись, «Мои записи» (перенос/отмена), «Контакты», оценка визита."""
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
    known = State()      # «Записать как Иван, +7...?» для повторного клиента
    comment = State()    # марка авто / размер шин (можно пропустить)
    confirm = State()


class Move(StatesGroup):
    day = State()
    time = State()


def available_days(db: Database, s: Settings, service_id: str) -> list[date]:
    today = datetime.now(s.tz).date()
    return [d for d in bookable_days(today, s.booking_days_ahead) if slots_for(db, s, service_id, d)]


def _start_dt(day: str, hhmm: str, s: Settings) -> datetime:
    return datetime.combine(date.fromisoformat(day), time(int(hhmm[:2]), int(hhmm[2:])), tzinfo=s.tz)


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
async def begin(message: Message, state: FSMContext, settings: Settings, db: Database):
    await state.clear()
    if db.count_active(message.chat.id, datetime.now(settings.tz)) >= settings.max_active_bookings:
        return await message.answer(
            f"У вас уже {settings.max_active_bookings} активные записи — это максимум. "
            "Перенесите или отмените одну из них в «📋 Мои записи», чтобы записаться снова."
        )
    await state.set_state(Booking.service)
    await message.answer("Выберите услугу:", reply_markup=kb.services_kb(settings))


@router.callback_query(Booking.service, F.data.startswith("svc:"))
async def pick_service(cb: CallbackQuery, state: FSMContext, settings: Settings, db: Database):
    service_id = cb.data.split(":")[1]
    if service_id not in settings.services:
        return await cb.answer("Неизвестная услуга")
    await state.update_data(service_id=service_id)
    days = available_days(db, settings, service_id)
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
async def pick_time(cb: CallbackQuery, state: FSMContext, db: Database):
    hhmm = cb.data.split(":")[1]
    await state.update_data(time=hhmm)
    known = db.get_client(cb.from_user.id)
    if known:  # повторный клиент: не спрашиваем имя и телефон заново
        await state.update_data(name=known[0], phone=known[1])
        await state.set_state(Booking.known)
        await cb.message.edit_text(f"Записать вас как {known[0]}, {known[1]}?", reply_markup=kb.known_client_kb())
    else:
        await state.set_state(Booking.name)
        await cb.message.edit_text("Как вас зовут?")
    await cb.answer()


@router.callback_query(Booking.known, F.data.startswith("me:"))
async def known_client(cb: CallbackQuery, state: FSMContext, settings: Settings):
    if cb.data == "me:yes":
        await ask_comment(cb.message, state, settings, edit=True)
    else:
        await state.set_state(Booking.name)
        await cb.message.edit_text("Как вас зовут?")
    await cb.answer()


async def ask_comment(message: Message, state: FSMContext, settings: Settings, edit: bool = False):
    await state.set_state(Booking.comment)
    text = settings.comment_prompt
    if edit:
        await message.edit_text(text, reply_markup=kb.skip_kb())
    else:
        await message.answer(text, reply_markup=kb.skip_kb())


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
    start = _start_dt(data["day"], data["time"], s)
    end = start + timedelta(minutes=service.duration_minutes)
    text = (
        "Проверьте запись:\n\n"
        f"🔧 {service.name} — {service.price} ₽\n🕒 {fmt_dt(start)} ({service.duration_minutes} мин)\n"
        + (f"{s.comment_icon} {data['comment']}\n" if data.get("comment") else "")
        + f"👤 {data['name']}\n📞 {data['phone']}\n📍 {s.address}"
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
    await message.answer("Спасибо!", reply_markup=kb.main_menu())
    await ask_comment(message, state, settings)


async def show_summary(message: Message, state: FSMContext, settings: Settings, edit: bool = False):
    await state.set_state(Booking.confirm)
    text, _, _ = _summary(await state.get_data(), settings)
    if edit:
        await message.edit_text(text, reply_markup=kb.confirm_kb())
    else:
        await message.answer(text, reply_markup=kb.confirm_kb())


@router.message(Booking.comment, F.text)
async def get_comment(message: Message, state: FSMContext, settings: Settings):
    await state.update_data(comment=message.text.strip()[:120])
    await show_summary(message, state, settings)


@router.callback_query(Booking.comment, F.data == "comment:skip")
async def skip_comment(cb: CallbackQuery, state: FSMContext, settings: Settings):
    await state.update_data(comment="")
    await show_summary(cb.message, state, settings, edit=True)
    await cb.answer()


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
    booking = db.create_booking(cb.from_user.id, data["name"], data["phone"], data["service_id"], start, end, data.get("comment", ""))
    if booking is None:  # кто-то успел раньше
        await state.set_state(Booking.day)
        days = available_days(db, settings, data["service_id"])
        await cb.message.edit_text("😔 Это время только что заняли. Выберите другое:", reply_markup=kb.days_kb(days))
        return await cb.answer()
    db.save_client(cb.from_user.id, data["name"], data["phone"])
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


# ===== Перенос записи =====
def _own_active(db: Database, booking_id: int, user_id: int):
    b = db.get(booking_id)
    return b if b and b.chat_id == user_id and b.status != "cancelled" else None


@router.callback_query(F.data.startswith("move:"))
async def move_start(cb: CallbackQuery, state: FSMContext, settings: Settings, db: Database):
    b = _own_active(db, int(cb.data.split(":")[1]), cb.from_user.id)
    if not b:
        return await cb.answer("Запись не найдена", show_alert=True)
    days = available_days(db, settings, b.service_id)
    if not days:
        return await cb.answer("Свободного времени на ближайшие дни нет", show_alert=True)
    await state.clear()
    await state.set_state(Move.day)
    await state.update_data(move_id=b.id, service_id=b.service_id)
    await cb.message.edit_text(booking_card(b, settings) + "\n\nНа какую дату перенести?", reply_markup=kb.days_kb(days, "mday", "move:cancel"))
    await cb.answer()


@router.callback_query(F.data == "move:cancel")
async def move_cancel(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    await cb.message.edit_text("Перенос отменён. Запись осталась без изменений.")
    await cb.answer()


@router.callback_query(Move.day, F.data.startswith("mday:"))
@router.callback_query(Move.time, F.data == "mback")
async def move_day(cb: CallbackQuery, state: FSMContext, settings: Settings, db: Database):
    data = await state.get_data()
    if cb.data.startswith("mday:"):
        await state.update_data(day=cb.data.split(":", 1)[1])
        data = await state.get_data()
    day = date.fromisoformat(data["day"])
    slots = slots_for(db, settings, data["service_id"], day)
    if not slots:
        return await cb.answer("На эту дату времени уже нет", show_alert=True)
    await state.set_state(Move.time)
    await cb.message.edit_text("Выберите новое время:", reply_markup=kb.times_kb(slots, "mtime", "mdays"))
    await cb.answer()


@router.callback_query(Move.time, F.data == "mdays")
async def move_days_again(cb: CallbackQuery, state: FSMContext, settings: Settings, db: Database):
    data = await state.get_data()
    await state.set_state(Move.day)
    await cb.message.edit_text("На какую дату перенести?", reply_markup=kb.days_kb(available_days(db, settings, data["service_id"]), "mday", "move:cancel"))
    await cb.answer()


@router.callback_query(Move.time, F.data.startswith("mtime:"))
async def move_time(cb: CallbackQuery, state: FSMContext, settings: Settings, db: Database):
    from .owner import notify_owner

    data = await state.get_data()
    b = _own_active(db, data["move_id"], cb.from_user.id)
    if not b:
        await state.clear()
        return await cb.answer("Запись не найдена", show_alert=True)
    old = booking_card(b, settings, with_status=False)
    start = _start_dt(data["day"], cb.data.split(":")[1], settings)
    end = start + timedelta(minutes=settings.services[b.service_id].duration_minutes)
    if start <= datetime.now(settings.tz) or not db.reschedule(b.id, start, end):
        return await cb.answer("Это время только что заняли, выберите другое", show_alert=True)
    await state.clear()
    b = db.get(b.id)
    await cb.message.edit_text("🔁 Запись перенесена и ждёт подтверждения.\n\n" + booking_card(b, settings))
    await notify_owner(cb.bot, settings, b, title=f"🔁 Перенос записи\nБыло:\n{old}\n\nСтало:")
    await cb.answer()


# ===== Оценка после визита =====
@router.callback_query(F.data.startswith("rate:"))
async def rate(cb: CallbackQuery, settings: Settings, db: Database):
    _, raw_id, raw_rating = cb.data.split(":")
    b = db.get(int(raw_id))
    if not b or b.chat_id != cb.from_user.id or b.status != "confirmed" or b.end > datetime.now(settings.tz):
        return await cb.answer("Оценить можно только состоявшийся визит", show_alert=True)
    if b.rating:
        return await cb.answer("Спасибо, оценка уже учтена")
    rating = max(1, min(5, int(raw_rating)))
    db.set_rating(b.id, rating)
    reply = "Спасибо за высокую оценку! Будем рады видеть вас снова 🙌" if rating >= 4 else \
        f"Спасибо за честность. Нам жаль, что что-то пошло не так. Управляющий свяжется с вами, или позвоните: {settings.phone}"
    await cb.message.edit_text(f"Ваша оценка: {'⭐' * rating}\n\n{reply}")
    await cb.bot.send_message(settings.owner_chat_id, f"{'⭐' * rating} Оценка визита\n\n" + booking_card(b, settings, with_client=True, with_status=False))
    await cb.answer()


# ===== Рассылки: отписка =====
@router.callback_query(F.data == "unsub")
async def unsubscribe(cb: CallbackQuery, db: Database):
    db.set_subscribed(cb.from_user.id, False)
    await cb.message.edit_reply_markup(reply_markup=None)
    await cb.answer("Вы отписались от рассылок. Напоминания о записях будут приходить как обычно.", show_alert=True)


@router.message()
async def fallback(message: Message):
    """Любое непонятное сообщение: подсказываем меню (подключается последним)."""
    await message.answer("Не совсем понял 🙂 Воспользуйтесь кнопками меню ниже.", reply_markup=kb.main_menu())
