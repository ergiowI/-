"""Telegram-бот студии йоги «Гармония»: расписание с местами, запись в мини-приложении или в чате, пробное занятие.

Запуск:
    pip install "aiogram==3.*"
    BOT_TOKEN=... ADMIN_CHAT_ID=... WEBAPP_URL=https://.../index.html python bot.py

WEBAPP_URL можно не задавать: тогда работает только запись в чате.
"""
import asyncio
import json
import os
import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path
from urllib.parse import quote

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (BotCommand, CallbackQuery, FSInputFile, InlineKeyboardButton, InlineKeyboardMarkup,
                           KeyboardButton, Message, ReplyKeyboardMarkup, WebAppInfo)

BOT_TOKEN = os.environ["BOT_TOKEN"]
ADMIN_CHAT_ID = int(os.environ["ADMIN_CHAT_ID"])  # чат студии: сюда приходят записи
WEBAPP_URL = os.environ.get("WEBAPP_URL", "")      # https-адрес webapp/index.html

NAME = "Студия йоги «Гармония»"
ADDRESS = "ул. Владимира Пчелинцева, 4"
MAP_URL = "https://yandex.ru/maps/?text=" + quote("Санкт-Петербург, улица Владимира Пчелинцева, 4")
CAPACITY = 12           # мест в группе
TRIAL, SINGLE = 300, 700
BANNER = Path(__file__).with_name("banner.png")

# Недельное расписание: день недели (0 = пн) → [(время, занятие)]. Тот же шаблон, что SCHEDULE в webapp/index.html
SCHEDULE = {
    0: [("08:00", "hatha_am"), ("19:00", "hatha"), ("20:30", "nidra")],
    1: [("10:00", "back"), ("19:00", "vinyasa")],
    2: [("08:00", "hatha_am"), ("19:00", "hatha"), ("20:30", "stretch")],
    3: [("10:00", "back"), ("19:00", "vinyasa")],
    4: [("19:00", "hatha"), ("20:30", "nidra")],
    5: [("11:00", "begin"), ("12:30", "stretch")],
    6: [("11:00", "soft"), ("18:00", "nidra")],
}
CLASSES = {  # код: (название, преподаватель, минут)
    "hatha_am": ("Утренняя хатха", "Анна", 60),
    "hatha":    ("Хатха-йога", "Анна", 75),
    "vinyasa":  ("Виньяса флоу", "Мария", 75),
    "back":     ("Йога для спины", "Анна", 60),
    "nidra":    ("Йога-нидра", "Мария", 45),
    "stretch":  ("Растяжка", "Мария", 60),
    "begin":    ("Йога для начинающих", "Анна", 75),
    "soft":     ("Мягкая йога", "Анна", 60),
}

WEEKDAYS = ["пн", "вт", "ср", "чт", "пт", "сб", "вс"]
MONTHS = ["января", "февраля", "марта", "апреля", "мая", "июня", "июля", "августа",
          "сентября", "октября", "ноября", "декабря"]
LINE = "━━━━━━━━━━━━━━━"

db = sqlite3.connect("yoga.db")
db.execute("""CREATE TABLE IF NOT EXISTS bookings (
    id INTEGER PRIMARY KEY, user_id INTEGER, name TEXT, day TEXT, time TEXT, cls TEXT, trial INTEGER,
    status TEXT DEFAULT 'new', reminded INTEGER DEFAULT 0, created TEXT)""")
db.execute("CREATE TABLE IF NOT EXISTS clients (user_id INTEGER PRIMARY KEY, name TEXT, phone TEXT)")
db.commit()


class Book(StatesGroup):
    day = State()
    cls = State()
    phone = State()


# ---------- helpers ----------

def kb(rows, cols=2):
    buttons = [InlineKeyboardButton(text=t, url=d[4:]) if d.startswith("url:") else InlineKeyboardButton(text=t, callback_data=d)
               for t, d in rows]
    return InlineKeyboardMarkup(inline_keyboard=[buttons[i:i + cols] for i in range(0, len(buttons), cols)])


def money(n):
    return f"{n:,}".replace(",", " ") + " ₽"


def human_day(day_iso):
    d = date.fromisoformat(day_iso)
    return f"{WEEKDAYS[d.weekday()]}, {d.day} {MONTHS[d.month - 1]}"


def class_at(day_iso, time):
    """Код занятия по расписанию на этот день и время, или None."""
    return dict(SCHEDULE.get(date.fromisoformat(day_iso).weekday(), [])).get(time)


def taken(day, time):
    return db.execute("SELECT COUNT(*) FROM bookings WHERE day=? AND time=? AND status!='cancelled'", (day, time)).fetchone()[0]


def already(user_id, day, time):
    return db.execute("SELECT 1 FROM bookings WHERE user_id=? AND day=? AND time=? AND status!='cancelled'",
                      (user_id, day, time)).fetchone() is not None


def is_new(user_id):
    """Новичок: ещё ни разу не записывался (пробное по специальной цене — один раз)."""
    return db.execute("SELECT 1 FROM bookings WHERE user_id=?", (user_id,)).fetchone() is None


def webapp_url(user_id):
    """Мини-приложению передаём занятость на неделю, свои записи и был ли уже пробный."""
    today = date.today().isoformat()
    rows = db.execute("SELECT day, time, COUNT(*) FROM bookings WHERE status!='cancelled' AND day>=? GROUP BY day, time",
                      (today,)).fetchall()
    mine = db.execute("SELECT id, day, time, cls, trial FROM bookings WHERE user_id=? AND status!='cancelled' AND day>=? "
                      "ORDER BY day, time", (user_id, today)).fetchall()
    taken_param = ",".join(f"{d}_{t}:{n}" for d, t, n in rows)
    my_param = ",".join(f"{i:04d}~{d}~{t}~{c}~" + ("trial" if tr else "single") for i, d, t, c, tr in mine)
    sep = "&" if "?" in WEBAPP_URL else "?"
    return f"{WEBAPP_URL}{sep}taken={taken_param}&my={my_param}&trial_used={0 if is_new(user_id) else 1}"


def main_keyboard(user_id):
    """Постоянная кнопка снизу: открывает мини-приложение (sendData работает только из такой кнопки)."""
    if not WEBAPP_URL:
        return None
    return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="🧘 Расписание и запись", web_app=WebAppInfo(url=webapp_url(user_id)))]],
                               resize_keyboard=True, is_persistent=True)


dp = Dispatcher()


# ---------- start ----------

@dp.message(CommandStart())
async def start(m: Message, state: FSMContext):
    await state.clear()
    caption = (f"<b>{NAME}</b>\n{ADDRESS}\n\n"
               "Хатха, виньяса, йога для спины и нидра в маленьких группах до 12 человек. "
               f"Первый раз у нас? Пробное занятие — {money(TRIAL)}.")
    buttons = kb([("🗓 Записаться в чате", "go"), ("📋 Мои занятия", "my"), ("📍 Как добраться", f"url:{MAP_URL}")], 1)
    if BANNER.exists():
        await m.answer_photo(FSInputFile(BANNER), caption=caption, parse_mode="HTML", reply_markup=buttons)
    else:
        await m.answer(caption, parse_mode="HTML", reply_markup=buttons)
    if WEBAPP_URL:
        await m.answer("Нажмите «🧘 Расписание и запись» внизу: там всё расписание на неделю и свободные места.",
                       reply_markup=main_keyboard(m.from_user.id))


# ---------- mini app ----------

@dp.message(F.web_app_data)
async def from_webapp(m: Message, state: FSMContext, bot: Bot):
    try:
        p = json.loads(m.web_app_data.data)
        if p.get("action") == "cancel":
            await cancel_booking(bot, int(p["no"]), m.from_user.id, m)
            return
        day, time = p["day"], p["time"]
        cls = class_at(day, time)
        if cls is None:
            raise ValueError
    except (KeyError, ValueError, TypeError):
        await m.answer("Не получилось прочитать запись, попробуйте ещё раз.", reply_markup=main_keyboard(m.from_user.id))
        return
    await state.set_data({"day": day, "time": time, "cls": cls})
    await confirm_or_ask_phone(m, state, bot, m.from_user.id)


# ---------- запись в чате ----------

@dp.callback_query(F.data == "go")
async def ask_day(c: CallbackQuery, state: FSMContext):
    await state.set_state(Book.day)
    days = []
    for i in range(7):
        d = date.today() + timedelta(days=i)
        if SCHEDULE.get(d.weekday()):
            label = "Сегодня" if i == 0 else "Завтра" if i == 1 else f"{WEEKDAYS[d.weekday()]} {d.day}"
            days.append((label, f"d:{d.isoformat()}"))
    await c.message.answer("На какой день записать?", reply_markup=kb(days, 4))
    await c.answer()


@dp.callback_query(Book.day, F.data.startswith("d:"))
async def ask_class(c: CallbackQuery, state: FSMContext):
    day = c.data[2:]
    now = datetime.now()
    rows = []
    for time, code in SCHEDULE.get(date.fromisoformat(day).weekday(), []):
        if datetime.fromisoformat(f"{day}T{time}") <= now:
            continue
        left = CAPACITY - taken(day, time)
        name, teacher, _ = CLASSES[code]
        if left > 0:
            rows.append((f"{time} · {name} · {teacher} · мест {left}", f"c:{time}"))
    if not rows:
        await c.answer("На этот день свободных мест нет, выберите другой", show_alert=True)
        return
    await state.update_data(day=day)
    await state.set_state(Book.cls)
    await c.message.edit_text(f"{human_day(day)}. Выберите занятие:", reply_markup=kb(rows, 1))
    await c.answer()


@dp.callback_query(Book.cls, F.data.startswith("c:"))
async def picked_class(c: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    time = c.data[2:]
    await state.update_data(time=time, cls=class_at(data["day"], time))
    await c.message.edit_reply_markup(reply_markup=None)
    await confirm_or_ask_phone(c.message, state, bot, c.from_user.id)
    await c.answer()


async def confirm_or_ask_phone(m: Message, state: FSMContext, bot: Bot, user_id: int):
    """Постоянного клиента записываем сразу, у нового один раз спрашиваем телефон."""
    client = db.execute("SELECT name, phone FROM clients WHERE user_id=?", (user_id,)).fetchone()
    if client:
        await finish_booking(m, state, bot, user_id, *client)
        return
    await state.set_state(Book.phone)
    await m.answer("Оставьте номер телефона: студия свяжется, если занятие перенесут. Спрашиваем один раз.",
                   reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="📱 Отправить мой номер", request_contact=True)]],
                                                    resize_keyboard=True, one_time_keyboard=True))


@dp.message(Book.phone)
async def got_phone(m: Message, state: FSMContext, bot: Bot):
    phone = m.contact.phone_number if m.contact else (m.text or "").strip()
    if len([ch for ch in phone if ch.isdigit()]) < 10:
        await m.answer("Нажмите кнопку «📱 Отправить мой номер» или напишите номер цифрами.")
        return
    name = (m.contact.first_name if m.contact else None) or m.from_user.first_name or "Клиент"
    db.execute("INSERT OR REPLACE INTO clients (user_id, name, phone) VALUES (?,?,?)", (m.from_user.id, name, phone))
    db.commit()
    await finish_booking(m, state, bot, m.from_user.id, name, phone)


async def finish_booking(m: Message, state: FSMContext, bot: Bot, user_id: int, name: str, phone: str):
    data = await state.get_data()
    await state.clear()
    day, time, code = data["day"], data["time"], data["cls"]
    if already(user_id, day, time):
        await m.answer("Вы уже записаны на это занятие 🙂", reply_markup=main_keyboard(user_id))
        return
    if taken(day, time) >= CAPACITY:
        await m.answer("Ой, последнее место только что заняли 😔 Выберите другое занятие: /start", reply_markup=main_keyboard(user_id))
        return
    trial = is_new(user_id)
    cur = db.execute("INSERT INTO bookings (user_id, name, day, time, cls, trial, created) VALUES (?,?,?,?,?,?,?)",
                     (user_id, name, day, time, code, int(trial), datetime.now().isoformat()))
    db.commit()
    bid = cur.lastrowid
    cname, teacher, minutes = CLASSES[code]
    pay = f"пробное, {money(TRIAL)}" if trial else f"{money(SINGLE)} или абонемент"
    await m.answer("Готово! 🪷", reply_markup=main_keyboard(user_id))
    await m.answer(f"✅ <b>Ждём вас на коврике</b> · № {bid:04d}\n{LINE}\n"
                   f"🧘 <b>{cname}</b>\n📅 {human_day(day)}, {time} · {minutes} мин\n👩‍🏫 {teacher}\n"
                   f"💳 {pay}, оплата на месте\n📍 {ADDRESS}\n{LINE}\n"
                   "Возьмите удобную одежду и воду, коврики есть в студии. Приходите за 10 минут.\n"
                   "За 2 часа пришлю напоминание.",
                   parse_mode="HTML", reply_markup=kb([("📍 Как добраться", f"url:{MAP_URL}"), ("❌ Отменить", f"cancel:{bid}")]))
    await bot.send_message(
        ADMIN_CHAT_ID,
        f"🧘 <b>Новая запись № {bid:04d}</b>\n<b>{cname}</b> · {human_day(day)}, {time}\n"
        f"👤 {name}{' · <b>новичок, пробное</b>' if trial else ''}\n"
        f"Мест занято: {taken(day, time)} из {CAPACITY}\n📞 {phone}",
        parse_mode="HTML", reply_markup=kb([("📋 Список группы", f"roster:{day}_{time}")]))


# ---------- мои занятия / отмена ----------

@dp.message(Command("my"))
@dp.callback_query(F.data == "my")
async def my_bookings(event):
    m = event.message if isinstance(event, CallbackQuery) else event
    rows = db.execute("SELECT id, day, time, cls FROM bookings WHERE user_id=? AND status!='cancelled' AND day>=? "
                      "ORDER BY day, time", (event.from_user.id, date.today().isoformat())).fetchall()
    if not rows:
        await m.answer("Вы пока никуда не записаны. Расписание: /start")
    for bid, day, time, code in rows:
        await m.answer(f"№ {bid:04d} · <b>{CLASSES[code][0]}</b>\n{human_day(day)}, {time} · {CLASSES[code][1]}",
                       parse_mode="HTML", reply_markup=kb([("❌ Отменить", f"cancel:{bid}")]))
    if isinstance(event, CallbackQuery):
        await event.answer()


async def cancel_booking(bot: Bot, bid: int, user_id: int, m: Message):
    row = db.execute("SELECT day, time, cls, name FROM bookings WHERE id=? AND user_id=? AND status!='cancelled'",
                     (bid, user_id)).fetchone()
    if not row:
        return False
    db.execute("UPDATE bookings SET status='cancelled' WHERE id=?", (bid,))
    db.commit()
    await m.answer("Запись отменена. Будем рады видеть вас на другом занятии: /start", reply_markup=main_keyboard(user_id))
    await bot.send_message(ADMIN_CHAT_ID, f"↩ {row[3]} отменил(а) запись № {bid:04d}: {CLASSES[row[2]][0]}, "
                                          f"{human_day(row[0])}, {row[1]}. Место свободно ({taken(row[0], row[1])}/{CAPACITY}).")
    return True


@dp.callback_query(F.data.startswith("cancel:"))
async def cancel(c: CallbackQuery, bot: Bot):
    if await cancel_booking(bot, int(c.data.split(":")[1]), c.from_user.id, c.message):
        await c.message.edit_reply_markup(reply_markup=None)
    await c.answer()


# ---------- для студии ----------

def is_admin(m: Message):
    return m.chat.id == ADMIN_CHAT_ID


def roster_text(day, time):
    code = class_at(day, time)
    rows = db.execute("SELECT b.name, b.trial, c.phone FROM bookings b LEFT JOIN clients c ON c.user_id=b.user_id "
                      "WHERE b.day=? AND b.time=? AND b.status!='cancelled' ORDER BY b.id", (day, time)).fetchall()
    head = f"📋 <b>{CLASSES[code][0] if code else 'Занятие'}</b> · {human_day(day)}, {time} · {len(rows)}/{CAPACITY}"
    if not rows:
        return head + "\nПока никто не записан."
    return head + "\n" + "\n".join(f"{i}. {n}{' 🌱 новичок' if tr else ''} · {ph or ''}" for i, (n, tr, ph) in enumerate(rows, 1))


@dp.callback_query(F.data.startswith("roster:"))
async def roster(c: CallbackQuery):
    if c.message.chat.id != ADMIN_CHAT_ID:
        return await c.answer()
    day, time = c.data[7:].split("_")
    await c.message.answer(roster_text(day, time), parse_mode="HTML")
    await c.answer()


async def day_overview(m: Message, day: date):
    lessons = SCHEDULE.get(day.weekday(), [])
    if not lessons:
        return await m.answer(f"На {human_day(day.isoformat())} занятий нет.")
    await m.answer("\n\n".join(roster_text(day.isoformat(), t) for t, _ in lessons), parse_mode="HTML")


@dp.message(Command("today"), is_admin)
async def today(m: Message):
    await day_overview(m, date.today())


@dp.message(Command("tomorrow"), is_admin)
async def tomorrow(m: Message):
    await day_overview(m, date.today() + timedelta(days=1))


@dp.message(Command("news"), is_admin)
async def news(m: Message, bot: Bot):
    """Новость всем клиентам студии: /news В субботу мастер-класс по растяжке!"""
    text = m.text.partition(" ")[2]
    if not text:
        return await m.answer("Напишите текст после команды, например:\n/news В субботу в 15:00 мастер-класс по растяжке!")
    users = [u for (u,) in db.execute("SELECT DISTINCT user_id FROM bookings").fetchall()]
    sent = 0
    for uid in users:
        try:
            await bot.send_message(uid, f"🪷 {NAME}\n\n{text}", reply_markup=kb([("🗓 Записаться", "go")]))
            sent += 1
        except Exception:
            pass
        await asyncio.sleep(0.1)
    await m.answer(f"Отправлено {sent} из {len(users)} клиентам.")


# ---------- напоминания ----------

async def reminders(bot: Bot):
    """Раз в 5 минут напоминает за 2 часа до занятия."""
    while True:
        now = datetime.now()
        rows = db.execute("SELECT id, user_id, day, time, cls FROM bookings WHERE status!='cancelled' AND reminded=0").fetchall()
        for bid, uid, day, time, code in rows:
            if timedelta(0) < datetime.fromisoformat(f"{day}T{time}") - now <= timedelta(hours=2):
                try:
                    await bot.send_message(uid, f"⏰ Сегодня в <b>{time}</b> — {CLASSES[code][0]} ({CLASSES[code][1]}).\n"
                                                f"📍 {ADDRESS}. Приходите за 10 минут 🧘",
                                           parse_mode="HTML",
                                           reply_markup=kb([("📍 Как добраться", f"url:{MAP_URL}"), ("❌ Не смогу", f"cancel:{bid}")]))
                except Exception:
                    pass
                db.execute("UPDATE bookings SET reminded=1 WHERE id=?", (bid,))
                db.commit()
        await asyncio.sleep(300)


async def main():
    bot = Bot(BOT_TOKEN)
    await bot.set_my_commands([BotCommand(command="start", description="Расписание и запись"),
                               BotCommand(command="my", description="Мои занятия")])
    asyncio.create_task(reminders(bot))
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
