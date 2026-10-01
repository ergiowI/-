from aiogram.types import InlineKeyboardButton as Btn, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

from .config import Settings


def main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📅 Записаться")], [KeyboardButton(text="📋 Мои записи"), KeyboardButton(text="📍 Контакты")]],
        resize_keyboard=True,
    )


def services_kb(s: Settings) -> InlineKeyboardMarkup:
    rows = [[Btn(text=f"{v.name} — {v.price} ₽", callback_data=f"svc:{v.id}")] for v in s.services.values()]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def days_kb(days: list) -> InlineKeyboardMarkup:
    from .texts import fmt_day

    rows = [[Btn(text=fmt_day(d), callback_data=f"day:{d.isoformat()}")] for d in days]
    rows.append([Btn(text="⬅️ Назад", callback_data="back:svc")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def times_kb(slots: list) -> InlineKeyboardMarkup:
    buttons = [Btn(text=s.strftime("%H:%M"), callback_data=f"time:{s.strftime('%H%M')}") for s in slots]
    rows = [buttons[i : i + 4] for i in range(0, len(buttons), 4)]
    rows.append([Btn(text="⬅️ Другая дата", callback_data="back:day")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def phone_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📱 Поделиться контактом", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def confirm_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[Btn(text="✅ Записаться", callback_data="confirm:yes"), Btn(text="✖️ Отмена", callback_data="confirm:no")]]
    )


def my_booking_kb(booking_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[Btn(text="❌ Отменить запись", callback_data=f"cancel:{booking_id}")]])


def owner_kb(booking_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[Btn(text="✅ Подтвердить", callback_data=f"own:ok:{booking_id}"), Btn(text="❌ Отменить", callback_data=f"own:no:{booking_id}")]]
    )
