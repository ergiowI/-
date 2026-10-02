"""Telegram-бот записи на шиномонтаж с расчётом цены до визита.

Запуск:
    pip install aiogram==3.*
    BOT_TOKEN=... ADMIN_CHAT_ID=... python bot.py
"""
import asyncio
import os
import sqlite3
from datetime import date, datetime, timedelta

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup,
                           KeyboardButton, Message, ReplyKeyboardMarkup, ReplyKeyboardRemove)

BOT_TOKEN = os.environ["BOT_TOKEN"]
ADMIN_CHAT_ID = int(os.environ["ADMIN_CHAT_ID"])  # куда приходят заявки (чат мастера)

ADDRESS = "Таллинское ш., 25А (рядом с «О’кей»)"
WORK_HOURS = range(10, 21)  # слоты с 10:00 до 20:00
SLOT_CAPACITY = 1           # сколько машин одновременно (число постов)

# Прайс: комплекс (снятие/установка + монтаж + балансировка), 4 колеса
PRICES = {
    "car":   {"R13": 1800, "R14": 1900, "R15": 2100, "R16": 2400, "R17": 2700, "R18": 3100, "R19": 3500, "R20": 3900},
    "cross": {"R15": 2500, "R16": 2800, "R17": 3100, "R18": 3500, "R19": 3900, "R20": 4400, "R21": 4900},
    "suv":   {"R16": 3200, "R17": 3600, "R18": 4000, "R19": 4500, "R20": 5000, "R21": 5600, "R22": 6200},
}
TYPES = {"car": "Легковой", "cross": "Кроссовер", "suv": "Внедорожник / минивэн"}
SERVICES = {
    "full":   ("Сезонная переобувка (комплекс)", 1.0),
    "wheels": ("Перестановка колёс в сборе", 0.45),
    "bal":    ("Только балансировка", 0.4),
}
EXTRAS = {"valves": ("Новые вентили, 4 шт", 400), "bags": ("Пакеты для шин, 4 шт", 200)}

db = sqlite3.connect("bookings.db")
db.execute("""CREATE TABLE IF NOT EXISTS bookings (
    id INTEGER PRIMARY KEY, user_id INTEGER, day TEXT, time TEXT, car TEXT, radius TEXT,
    service TEXT, extras TEXT, price INTEGER, phone TEXT, status TEXT DEFAULT 'new',
    reminded INTEGER DEFAULT 0, created TEXT)""")
db.commit()


class Booking(StatesGroup):
    type = State()
    radius = State()
    service = State()
    extras = State()
    day = State()
    time = State()
    phone = State()


def kb(rows, cols=2):
    buttons = [InlineKeyboardButton(text=t, callback_data=d) for t, d in rows]
    return InlineKeyboardMarkup(inline_keyboard=[buttons[i:i + cols] for i in range(0, len(buttons), cols)])


def calc(data):
    base = PRICES[data["type"]][data["radius"]]
    svc = round(base * SERVICES[data["service"]][1] / 50) * 50
    extras = sum(EXTRAS[e][1] for e in data.get("extras", []))
    return svc, svc + extras


def busy_count(day, time):
    return db.execute("SELECT COUNT(*) FROM bookings WHERE day=? AND time=? AND status!='cancelled'",
                      (day, time)).fetchone()[0]


dp = Dispatcher()


@dp.message(CommandStart())
async def start(m: Message, state: FSMContext):
    await state.clear()
    await m.answer(f"Здравствуйте! Это шиномонтаж на {ADDRESS}.\n"
                   "Запишу вас за минуту и сразу покажу точную цену.",
                   reply_markup=kb([("🛞 Записаться", "go"), ("📍 Как доехать", "where")], 1))


@dp.callback_query(F.data == "where")
async def where(c: CallbackQuery):
    await c.message.answer(f"{ADDRESS}\nРаботаем ежедневно 9:00–21:00.")
    await c.answer()


@dp.callback_query(F.data == "go")
async def ask_type(c: CallbackQuery, state: FSMContext):
    await state.set_state(Booking.type)
    await c.message.answer("Какая у вас машина?", reply_markup=kb([(v, f"t:{k}") for k, v in TYPES.items()], 1))
    await c.answer()


@dp.callback_query(Booking.type, F.data.startswith("t:"))
async def ask_radius(c: CallbackQuery, state: FSMContext):
    t = c.data[2:]
    await state.update_data(type=t)
    await state.set_state(Booking.radius)
    await c.message.answer("Какой радиус дисков? Он написан на шине, например 205/55 R16.",
                           reply_markup=kb([(r, f"r:{r}") for r in PRICES[t]], 4))
    await c.answer()


@dp.callback_query(Booking.radius, F.data.startswith("r:"))
async def ask_service(c: CallbackQuery, state: FSMContext):
    await state.update_data(radius=c.data[2:])
    await state.set_state(Booking.service)
    await c.message.answer("Что нужно сделать?", reply_markup=kb([(v[0], f"s:{k}") for k, v in SERVICES.items()], 1))
    await c.answer()


@dp.callback_query(Booking.service, F.data.startswith("s:"))
async def ask_extras(c: CallbackQuery, state: FSMContext):
    await state.update_data(service=c.data[2:])
    await state.set_state(Booking.extras)
    await c.message.answer("Добавить что-нибудь?", reply_markup=kb([
        ("Вентили +400 ₽", "e:valves"), ("Пакеты +200 ₽", "e:bags"),
        ("Вентили и пакеты +600 ₽", "e:valves,bags"), ("Ничего не нужно", "e:")]))
    await c.answer()


@dp.callback_query(Booking.extras, F.data.startswith("e:"))
async def show_price(c: CallbackQuery, state: FSMContext):
    extras = [e for e in c.data[2:].split(",") if e]
    await state.update_data(extras=extras)
    data = await state.get_data()
    svc, total = calc(data)
    lines = [f"{SERVICES[data['service']][0]}, {TYPES[data['type']].lower()} {data['radius']}: {svc} ₽"]
    lines += [f"{EXTRAS[e][0]}: {EXTRAS[e][1]} ₽" for e in extras]
    await c.message.answer("\n".join(lines) + f"\n\n<b>Итого: {total} ₽</b>\n"
                           "Цена фиксируется при записи и на месте не меняется.", parse_mode="HTML")
    await state.set_state(Booking.day)
    days = []
    for i in range(4):
        d = date.today() + timedelta(days=i)
        label = ("Сегодня " if i == 0 else "Завтра " if i == 1 else "") + d.strftime("%d.%m")
        days.append((label, f"d:{d.isoformat()}"))
    await c.message.answer("Выберите день:", reply_markup=kb(days))
    await c.answer()


@dp.callback_query(Booking.day, F.data.startswith("d:"))
async def ask_time(c: CallbackQuery, state: FSMContext):
    day = c.data[2:]
    now = datetime.now()
    free = []
    for h in WORK_HOURS:
        t = f"{h:02d}:00"
        if day == now.date().isoformat() and h <= now.hour:
            continue
        if busy_count(day, t) < SLOT_CAPACITY:
            free.append((t, f"h:{t}"))
    if not free:
        await c.answer("На этот день всё занято, выберите другой", show_alert=True)
        return
    await state.update_data(day=day)
    await state.set_state(Booking.time)
    await c.message.answer("Свободное время:", reply_markup=kb(free, 4))
    await c.answer()


@dp.callback_query(Booking.time, F.data.startswith("h:"))
async def ask_phone(c: CallbackQuery, state: FSMContext):
    await state.update_data(time=c.data[2:])
    await state.set_state(Booking.phone)
    await c.message.answer("Оставьте номер, чтобы мастер мог связаться, если что-то изменится.",
                           reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="📱 Отправить мой номер", request_contact=True)]],
                                                            resize_keyboard=True, one_time_keyboard=True))
    await c.answer()


@dp.message(Booking.phone)
async def finish(m: Message, state: FSMContext, bot: Bot):
    phone = m.contact.phone_number if m.contact else (m.text or "").strip()
    data = await state.get_data()
    if busy_count(data["day"], data["time"]) >= SLOT_CAPACITY:
        await state.set_state(Booking.day)
        await m.answer("Это время только что заняли, выберите другое: /start", reply_markup=ReplyKeyboardRemove())
        return
    svc, total = calc(data)
    cur = db.execute("INSERT INTO bookings (user_id, day, time, car, radius, service, extras, price, phone, created) "
                     "VALUES (?,?,?,?,?,?,?,?,?,?)",
                     (m.from_user.id, data["day"], data["time"], data["type"], data["radius"], data["service"],
                      ",".join(data["extras"]), total, phone, datetime.now().isoformat()))
    db.commit()
    bid = cur.lastrowid
    await state.clear()
    day_h = datetime.fromisoformat(data["day"]).strftime("%d.%m")
    await m.answer(f"✅ Вы записаны\n{day_h}, {data['time']}\n{SERVICES[data['service']][0]}, {data['radius']}\n"
                   f"К оплате: {total} ₽\n\n{ADDRESS}. За 2 часа напомню о визите.",
                   reply_markup=ReplyKeyboardRemove())
    await m.answer("Если планы изменятся:", reply_markup=kb([("Отменить запись", f"cancel:{bid}")], 1))
    extras = ", ".join(EXTRAS[e][0] for e in data["extras"]) or "—"
    await bot.send_message(ADMIN_CHAT_ID,
                           f"🛞 Новая запись #{bid}\nКогда: {day_h}, {data['time']}\n"
                           f"Машина: {TYPES[data['type']]}, {data['radius']}\nУслуга: {SERVICES[data['service']][0]}\n"
                           f"Доп.: {extras}\nЦена: {total} ₽ (клиент видел и согласен)\nТелефон: {phone}",
                           reply_markup=kb([("✔ Подтвердить", f"ok:{bid}"), ("✖ Отказать", f"no:{bid}")]))


@dp.callback_query(F.data.startswith("cancel:"))
async def cancel(c: CallbackQuery, bot: Bot):
    bid = int(c.data.split(":")[1])
    row = db.execute("SELECT day, time FROM bookings WHERE id=? AND user_id=?", (bid, c.from_user.id)).fetchone()
    if row:
        db.execute("UPDATE bookings SET status='cancelled' WHERE id=?", (bid,))
        db.commit()
        await c.message.answer("Запись отменена.")
        await bot.send_message(ADMIN_CHAT_ID, f"❌ Клиент отменил запись #{bid} ({row[0]} {row[1]}), окно свободно.")
    await c.answer()


@dp.callback_query(F.data.regexp(r"^(ok|no):\d+$"))
async def admin_decision(c: CallbackQuery, bot: Bot):
    if c.message.chat.id != ADMIN_CHAT_ID:
        return await c.answer()
    action, bid = c.data.split(":")
    row = db.execute("SELECT user_id, day, time FROM bookings WHERE id=?", (int(bid),)).fetchone()
    if not row:
        return await c.answer("Запись не найдена")
    if action == "ok":
        db.execute("UPDATE bookings SET status='confirmed' WHERE id=?", (int(bid),))
        await bot.send_message(row[0], f"Мастер подтвердил запись на {row[2]}. Ждём вас!")
    else:
        db.execute("UPDATE bookings SET status='cancelled' WHERE id=?", (int(bid),))
        await bot.send_message(row[0], "К сожалению, на это время принять не получится. Выберите другое: /start")
    db.commit()
    await c.message.edit_reply_markup(reply_markup=None)
    await c.answer("Готово")


async def reminders(bot: Bot):
    """Раз в 5 минут напоминает клиентам за 2 часа до визита."""
    while True:
        now = datetime.now()
        rows = db.execute("SELECT id, user_id, day, time FROM bookings "
                          "WHERE status!='cancelled' AND reminded=0").fetchall()
        for bid, uid, day, t in rows:
            visit = datetime.fromisoformat(f"{day}T{t}")
            if timedelta(0) < visit - now <= timedelta(hours=2):
                try:
                    await bot.send_message(uid, f"Напоминаю: сегодня в {t} вы записаны на шиномонтаж, {ADDRESS}.")
                except Exception:
                    pass
                db.execute("UPDATE bookings SET reminded=1 WHERE id=?", (bid,))
                db.commit()
        await asyncio.sleep(300)


async def main():
    bot = Bot(BOT_TOKEN)
    asyncio.create_task(reminders(bot))
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
