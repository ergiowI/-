"""Telegram-бот онлайн-записи для «TRUEMAN Barbershop» (пр. Ветеранов, 196).

Запись через мини-приложение (webapp/index.html) или по шагам в чате, квитанция с номером, «Мои записи», отмена,
напоминание перед визитом, кнопки «Подтвердить / Отказать» у владельца, расписание /today и /tomorrow,
приглашение записаться снова через 21 день после визита.

Запуск:
    pip install "aiogram==3.*"
    BOT_TOKEN=... ADMIN_CHAT_ID=... WEBAPP_URL=https://.../index.html python bot.py

WEBAPP_URL можно не задавать: тогда работает только запись в чате.
Услуги, цены и часы — в CONFIG ниже (те же, что в demo.html).
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
ADMIN_CHAT_ID = int(os.environ["ADMIN_CHAT_ID"])  # чат владельца: сюда приходят заявки
WEBAPP_URL = os.environ.get("WEBAPP_URL", "")      # https-адрес webapp/index.html

CONFIG = {'name': 'TRUEMAN Barbershop',
 'address': 'пр. Ветеранов, 196',
 'icon': '💈',
 'hoursText': 'Ежедневно 10:00–22:00',
 'welcome': 'Запишу к барберу за минуту: услуга, барбер, время. За 2 часа напомню, а через 3 недели подскажу, что '
            'пора снова.',
 'askService': 'Что делаем?',
 'remindWhen': 'за 2 часа',
 'remindHours': 2,
 'courseWord': 'Курс',
 'masterLabel': 'Барбер',
 'hours': ['10:00',
           '11:00',
           '12:00',
           '13:00',
           '14:00',
           '15:00',
           '16:00',
           '17:00',
           '18:00',
           '19:00',
           '20:00',
           '21:00'],
 'masters': [{'n': 'Денис', 'r': 'топ-барбер'}, {'n': 'Кирилл', 'r': 'барбер'}, {'n': 'Влад', 'r': 'барбер'}],
 'follow': {'mode': 'days',
            'days': 21,
            'text': 'Здравствуйте! Это {name}. Прошло 3 недели после стрижки — самое время поправить форму. Записать '
                    'вас?'},
 'services': [{'k': 'cut', 'n': 'Мужская стрижка', 'p': 1800, 'd': '60 мин'},
              {'k': 'combo', 'n': 'Стрижка + борода', 'p': 2700, 'd': '90 мин'},
              {'k': 'beard', 'n': 'Борода и усы', 'p': 1200, 'd': '45 мин'},
              {'k': 'shave', 'n': 'Бритьё опасной бритвой', 'p': 1500, 'd': 'горячее полотенце'},
              {'k': 'fs', 'n': 'Отец + сын', 'p': 2900, 'd': 'две стрижки, −10%'}]}

NAME = CONFIG["name"]
ADDRESS = CONFIG["address"]
MAP_URL = "https://yandex.ru/maps/?text=" + quote("Санкт-Петербург, " + ADDRESS)
SERVICES = {s["k"]: s for s in CONFIG["services"]}
BRANCHES = CONFIG.get("branches") or []          # [[коротко, полный адрес], ...]
OPTS = CONFIG.get("opts")                        # {"label": ..., "list": [[название, коэффициент цены], ...]}
MASTERS = CONFIG.get("masters") or []            # [{"n": имя, "r": роль, "b": филиал, "cats": [...]}]
HOURS = CONFIG["hours"]                          # ["10:00", "11:00", ...]
CLOSED = {(d + 6) % 7 for d in CONFIG.get("closedDays", [])}  # в конфиге 0 = воскресенье (как в JS)
FOLLOW = CONFIG.get("follow")                    # {"mode": "season"} или {"mode": "days", "days": N}
REMIND_BEFORE = timedelta(hours=CONFIG.get("remindHours", 2))
BANNER = Path(__file__).with_name("banner.png")

WEEKDAYS = ["пн", "вт", "ср", "чт", "пт", "сб", "вс"]
MONTHS = ["января", "февраля", "марта", "апреля", "мая", "июня", "июля", "августа",
          "сентября", "октября", "ноября", "декабря"]
LINE = "━━━━━━━━━━━━━━━"

db = sqlite3.connect("bookings.db")
db.execute("""CREATE TABLE IF NOT EXISTS bookings (
    id INTEGER PRIMARY KEY, user_id INTEGER, branch INTEGER, opt INTEGER, service TEXT, master INTEGER,
    day TEXT, time TEXT, price INTEGER, phone TEXT, status TEXT DEFAULT 'new',
    reminded INTEGER DEFAULT 0, visited INTEGER DEFAULT 0, followed INTEGER DEFAULT 0, created TEXT)""")
# Курсы и абонементы: сколько сеансов куплено и сколько уже пройдено
db.execute("""CREATE TABLE IF NOT EXISTS courses (
    id INTEGER PRIMARY KEY, user_id INTEGER, service TEXT, total INTEGER, used INTEGER DEFAULT 0, created TEXT)""")
db.execute("CREATE TABLE IF NOT EXISTS optout (user_id INTEGER PRIMARY KEY)")
db.commit()


class Booking(StatesGroup):
    branch = State()
    opt = State()
    service = State()
    master = State()
    day = State()
    time = State()
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


def human_date(d):
    return f"{d.day} {MONTHS[d.month - 1]}"


def calc(data):
    s = SERVICES[data["service"]]
    k = OPTS["list"][data.get("opt", 0)][1] if OPTS else 1
    return round(s["p"] * k / 50) * 50


def price_text(data):
    s = SERVICES[data["service"]]
    return "бесплатно" if s["p"] == 0 else ("от " if s.get("from") else "") + money(calc(data))


def masters_for(branch, service=None):
    cat = SERVICES[service].get("c") if service else None
    return [i for i, m in enumerate(MASTERS)
            if m.get("b", branch) == branch and (not cat or not m.get("cats") or cat in m["cats"])]


def capacity(branch):
    return max(1, len([m for m in MASTERS if m.get("b", branch) == branch]))


def slot_free(branch, master, day, time):
    rows = db.execute("SELECT master FROM bookings WHERE branch=? AND day=? AND time=? AND status!='cancelled'",
                      (branch, day, time)).fetchall()
    if len(rows) >= capacity(branch):
        return False
    return master < 0 or all(m != master for (m,) in rows)


def busy_slots():
    """Полностью занятые слоты на неделю вперёд для мини-приложения: b0_2026-10-03_11:00,..."""
    rows = db.execute("SELECT branch, day, time, COUNT(*) FROM bookings WHERE status!='cancelled' AND day>=? "
                      "GROUP BY branch, day, time", (date.today().isoformat(),)).fetchall()
    return ",".join(f"b{b}_{d}_{t}" for b, d, t, n in rows if n >= capacity(b))


def my_param(user_id):
    rows = db.execute("SELECT id, day, time, service, price FROM bookings WHERE user_id=? AND status!='cancelled' "
                      "AND day>=? ORDER BY day, time", (user_id, date.today().isoformat())).fetchall()
    return ",".join(f"{bid:04d}~{d}~{t}~{s}~{p}" for bid, d, t, s, p in rows)


def main_keyboard(user_id=None):
    """Постоянная кнопка снизу: открывает мини-приложение (sendData работает только из такой кнопки)."""
    if not WEBAPP_URL:
        return None
    sep = "&" if "?" in WEBAPP_URL else "?"
    url = f"{WEBAPP_URL}{sep}busy={busy_slots()}"
    if user_id is not None:
        url += f"&my={my_param(user_id)}"
    return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text=f"{CONFIG['icon']} Записаться онлайн", web_app=WebAppInfo(url=url))]],
                               resize_keyboard=True, is_persistent=True)


def active_course(user_id):
    return db.execute("SELECT id, service, total, used FROM courses WHERE user_id=? AND used<total ORDER BY id DESC LIMIT 1",
                      (user_id,)).fetchone()


def next_season(day_iso):
    d = date.fromisoformat(day_iso)
    if 3 <= d.month <= 8:
        return date(d.year, 10, 1), "зимнюю"
    return date(d.year + 1 if d.month >= 9 else d.year, 4, 1), "летнюю"


def details(data):
    lines = []
    if BRANCHES:
        lines.append(f"📍 {BRANCHES[data['branch']][1]}")
    opt = f", {OPTS['list'][data['opt']][0].lower()}" if OPTS else ""
    lines.append(f"{CONFIG['icon']} {SERVICES[data['service']]['n']}{opt}")
    if MASTERS:
        lines.append(f"👤 {MASTERS[data['master']]['n'] if data['master'] >= 0 else 'любой свободный'}")
    return "\n".join(lines)


def days_keyboard():
    days = []
    for i in range(7):
        d = date.today() + timedelta(days=i)
        if d.weekday() in CLOSED:
            continue
        label = "Сегодня" if i == 0 else "Завтра" if i == 1 else f"{WEEKDAYS[d.weekday()]} {d.day}"
        days.append((label, f"d:{d.isoformat()}"))
    return kb(days, 4)


dp = Dispatcher()


# ---------- start ----------

@dp.message(CommandStart())
async def start(m: Message, state: FSMContext):
    await state.clear()
    caption = f"<b>{NAME}</b>\n{ADDRESS} · {CONFIG['hoursText']}\n\n{CONFIG['welcome']}"
    rows = [("💬 Записаться в чате", "go"), ("📋 Мои записи", "my")]
    if any(s.get("course") for s in SERVICES.values()):
        rows.append(("🎟 Мой абонемент", "course"))
    rows.append(("📍 Как добраться", f"url:{MAP_URL}"))
    if BANNER.exists():
        await m.answer_photo(FSInputFile(BANNER), caption=caption, parse_mode="HTML", reply_markup=kb(rows, 1))
    else:
        await m.answer(caption, parse_mode="HTML", reply_markup=kb(rows, 1))
    if WEBAPP_URL:
        await m.answer(f"Нажмите «{CONFIG['icon']} Записаться онлайн» внизу: там всё свободное время и цены.",
                       reply_markup=main_keyboard(m.from_user.id))


# ---------- мини-приложение ----------

@dp.message(F.web_app_data)
async def from_webapp(m: Message, state: FSMContext, bot: Bot):
    try:
        p = json.loads(m.web_app_data.data)
        if p.get("action") == "cancel":
            await cancel_booking(bot, int(p["no"]), m.from_user.id, m)
            return
        data = {"branch": int(p.get("branch", 0)), "opt": int(p.get("opt", 0)), "service": p["svc"],
                "master": int(p.get("master", -1)), "day": p["day"], "time": p["time"]}
        SERVICES[data["service"]]  # значения проверяем по своему прайсу
        assert data["time"] in HOURS and 0 <= data["branch"] < max(1, len(BRANCHES))
        assert not OPTS or 0 <= data["opt"] < len(OPTS["list"])
        assert data["master"] < 0 or data["master"] in masters_for(data["branch"], data["service"])
        date.fromisoformat(data["day"])
    except (KeyError, ValueError, TypeError, AssertionError):
        await m.answer("Не получилось прочитать заявку, попробуйте ещё раз.", reply_markup=main_keyboard(m.from_user.id))
        return
    if not slot_free(data["branch"], data["master"], data["day"], data["time"]):
        await m.answer("Это время только что заняли 😔 Откройте запись ещё раз и выберите другое.",
                       reply_markup=main_keyboard(m.from_user.id))
        return
    await state.set_data(data)  # цену пересчитываем сами, присланной не доверяем
    await ask_phone(m, state)


# ---------- запись в чате ----------

@dp.callback_query(F.data == "go")
async def go(c: CallbackQuery, state: FSMContext):
    await state.set_data({"branch": 0, "opt": 0, "master": -1})
    if BRANCHES:
        await state.set_state(Booking.branch)
        await c.message.answer("Куда вам удобнее?", reply_markup=kb([(b[1], f"b:{i}") for i, b in enumerate(BRANCHES)], 1))
    else:
        await ask_opt(c.message, state)
    await c.answer()


@dp.callback_query(Booking.branch, F.data.startswith("b:"))
async def picked_branch(c: CallbackQuery, state: FSMContext):
    await state.update_data(branch=int(c.data[2:]))
    await c.message.edit_reply_markup(reply_markup=None)
    await ask_opt(c.message, state)
    await c.answer()


async def ask_opt(m: Message, state: FSMContext):
    if not OPTS:
        return await ask_service(m, state)
    await state.set_state(Booking.opt)
    await m.answer(f"{OPTS['label']}?", reply_markup=kb([(o[0], f"o:{i}") for i, o in enumerate(OPTS["list"])], 1))


@dp.callback_query(Booking.opt, F.data.startswith("o:"))
async def picked_opt(c: CallbackQuery, state: FSMContext):
    await state.update_data(opt=int(c.data[2:]))
    await c.message.edit_reply_markup(reply_markup=None)
    await ask_service(c.message, state)
    await c.answer()


async def ask_service(m: Message, state: FSMContext):
    data = await state.get_data()
    await state.set_state(Booking.service)
    rows = [(f"{s['n']} · {price_text({**data, 'service': k})}", f"s:{k}") for k, s in SERVICES.items()]
    await m.answer(CONFIG["askService"], reply_markup=kb(rows, 1))


@dp.callback_query(Booking.service, F.data.startswith("s:"))
async def picked_service(c: CallbackQuery, state: FSMContext):
    await state.update_data(service=c.data[2:])
    data = await state.get_data()
    await c.message.edit_reply_markup(reply_markup=None)
    ids = masters_for(data["branch"], data["service"]) if MASTERS else []
    if ids:
        await state.set_state(Booking.master)
        await c.message.answer(f"{CONFIG.get('masterLabel', 'Мастер')}?",
                               reply_markup=kb([("Любой свободный", "m:-1")] + [(f"{MASTERS[i]['n']} · {MASTERS[i]['r']}", f"m:{i}") for i in ids], 1))
    else:
        await ask_day(c.message, state)
    await c.answer()


@dp.callback_query(Booking.master, F.data.startswith("m:"))
async def picked_master(c: CallbackQuery, state: FSMContext):
    await state.update_data(master=int(c.data[2:]))
    await c.message.edit_reply_markup(reply_markup=None)
    await ask_day(c.message, state)
    await c.answer()


async def ask_day(m: Message, state: FSMContext):
    data = await state.get_data()
    await state.set_state(Booking.day)
    await m.answer(f"💰 Стоимость: <b>{price_text(data)}</b>\n\nВыберите день:", parse_mode="HTML", reply_markup=days_keyboard())


@dp.callback_query(Booking.day, F.data.startswith("d:"))
async def ask_time(c: CallbackQuery, state: FSMContext):
    day, data, now = c.data[2:], await state.get_data(), datetime.now()
    free = [(t, f"h:{t}") for t in HOURS
            if not (day == now.date().isoformat() and int(t[:2]) <= now.hour) and slot_free(data["branch"], data["master"], day, t)]
    if not free:
        await c.answer("На этот день всё занято, выберите другой", show_alert=True)
        return
    await state.update_data(day=day)
    await state.set_state(Booking.time)
    await c.message.edit_text(f"{human_day(day)}. Свободное время:", reply_markup=kb(free, 4))
    await c.answer()


@dp.callback_query(Booking.time, F.data.startswith("h:"))
async def picked_time(c: CallbackQuery, state: FSMContext):
    await state.update_data(time=c.data[2:])
    await c.message.edit_reply_markup(reply_markup=None)
    await ask_phone(c.message, state)
    await c.answer()


async def ask_phone(m: Message, state: FSMContext):
    await state.set_state(Booking.phone)
    await m.answer("Последний шаг: оставьте номер, чтобы с вами могли связаться, если что-то изменится.",
                   reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="📱 Отправить мой номер", request_contact=True)]],
                                                    resize_keyboard=True, one_time_keyboard=True))


@dp.message(Booking.phone)
async def finish(m: Message, state: FSMContext, bot: Bot):
    phone = m.contact.phone_number if m.contact else (m.text or "").strip()
    if len([ch for ch in phone if ch.isdigit()]) < 10:
        await m.answer("Нажмите кнопку «📱 Отправить мой номер» или напишите номер цифрами.")
        return
    data = await state.get_data()
    await state.clear()
    if not slot_free(data["branch"], data["master"], data["day"], data["time"]):
        await m.answer("Это время только что заняли 😔 Выберите другое: /start", reply_markup=main_keyboard(m.from_user.id))
        return
    total = 0 if SERVICES[data["service"]]["p"] == 0 else calc(data)
    cur = db.execute("INSERT INTO bookings (user_id, branch, opt, service, master, day, time, price, phone, created) "
                     "VALUES (?,?,?,?,?,?,?,?,?,?)",
                     (m.from_user.id, data["branch"], data["opt"], data["service"], data["master"], data["day"], data["time"],
                      total, phone, datetime.now().isoformat()))
    bid = cur.lastrowid
    course_line = ""
    svc = SERVICES[data["service"]]
    if svc.get("course"):
        db.execute("INSERT INTO courses (user_id, service, total, created) VALUES (?,?,?,?)",
                   (m.from_user.id, data["service"], svc["course"], datetime.now().isoformat()))
        course_line = f"\n🎟 {CONFIG.get('courseWord', 'Курс')}: {svc['course']} сеансов, это первый"
    elif (c := active_course(m.from_user.id)):
        course_line = f"\n🎟 Сеанс {c[3] + 1} из {c[2]}"
    db.commit()
    where = BRANCHES[data["branch"]][1] if BRANCHES else ADDRESS
    await m.answer("Готово! 🎉", reply_markup=main_keyboard(m.from_user.id))
    await m.answer(f"✅ <b>Вы записаны</b> · № {bid:04d}\n{LINE}\n📅 <b>{human_day(data['day'])} · {data['time']}</b>\n"
                   f"{details(data)}{course_line}\n{LINE}\n💰 <b>{price_text(data)}</b>\n📍 {where}\n\n"
                   f"Напомню {CONFIG['remindWhen']}.",
                   parse_mode="HTML", reply_markup=kb([("📍 Маршрут", f"url:{MAP_URL}"), ("❌ Отменить", f"cancel:{bid}")]))
    await bot.send_message(
        ADMIN_CHAT_ID,
        f"{CONFIG['icon']} <b>Новая запись № {bid:04d}</b>\n{LINE}\n📅 <b>{human_day(data['day'])} · {data['time']}</b>\n"
        f"{details(data)}\n💰 {price_text(data)}{course_line}\n📞 {phone}",
        parse_mode="HTML", reply_markup=kb([("✔ Подтвердить", f"ok:{bid}"), ("✖ Отказать", f"no:{bid}")]))


# ---------- мои записи / абонемент / отмена ----------

@dp.message(Command("my"))
@dp.callback_query(F.data == "my")
async def my_bookings(event):
    m = event.message if isinstance(event, CallbackQuery) else event
    rows = db.execute("SELECT id, day, time, service, price FROM bookings WHERE user_id=? AND status!='cancelled' "
                      "AND day>=? ORDER BY day, time", (event.from_user.id, date.today().isoformat())).fetchall()
    if not rows:
        await m.answer("Активных записей нет. Записаться: /start")
    for bid, day, t, svc, price in rows:
        await m.answer(f"№ {bid:04d} · <b>{human_day(day)}, {t}</b>\n{SERVICES[svc]['n']} · {money(price)}",
                       parse_mode="HTML", reply_markup=kb([("❌ Отменить", f"cancel:{bid}")]))
    if isinstance(event, CallbackQuery):
        await event.answer()


@dp.message(Command("course"))
@dp.callback_query(F.data == "course")
async def my_course(event):
    m = event.message if isinstance(event, CallbackQuery) else event
    c = active_course(event.from_user.id)
    if not c:
        await m.answer("Активного абонемента нет. Купить курс со скидкой можно при записи: /start")
    else:
        await m.answer(f"🎟 <b>{SERVICES[c[1]]['n']}</b>\nПройдено {c[3]} из {c[2]}, осталось <b>{c[2] - c[3]}</b>.",
                       parse_mode="HTML", reply_markup=kb([("📅 Записаться на следующий", "go")], 1))
    if isinstance(event, CallbackQuery):
        await event.answer()


async def cancel_booking(bot: Bot, bid: int, user_id: int, m: Message):
    row = db.execute("SELECT day, time FROM bookings WHERE id=? AND user_id=? AND status!='cancelled'", (bid, user_id)).fetchone()
    if not row:
        return False
    db.execute("UPDATE bookings SET status='cancelled' WHERE id=?", (bid,))
    db.commit()
    await m.answer("Запись отменена. Будем рады видеть вас в другой раз: /start", reply_markup=main_keyboard(user_id))
    await bot.send_message(ADMIN_CHAT_ID, f"❌ Клиент отменил запись № {bid:04d} ({human_day(row[0])}, {row[1]}), окно свободно.")
    return True


@dp.callback_query(F.data.startswith("cancel:"))
async def cancel(c: CallbackQuery, bot: Bot):
    if await cancel_booking(bot, int(c.data.split(":")[1]), c.from_user.id, c.message):
        await c.message.edit_reply_markup(reply_markup=None)
    await c.answer()


@dp.callback_query(F.data == "optout")
async def optout(c: CallbackQuery):
    db.execute("INSERT OR IGNORE INTO optout (user_id) VALUES (?)", (c.from_user.id,))
    db.commit()
    await c.answer("Хорошо, больше не буду напоминать", show_alert=True)


# ---------- для владельца ----------

def is_admin(m: Message):
    return m.chat.id == ADMIN_CHAT_ID


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
        await bot.send_message(row[0], f"👍 Запись подтверждена: {human_day(row[1])}, {row[2]}. Ждём вас!")
        mark = "✔ Подтверждено"
    else:
        db.execute("UPDATE bookings SET status='cancelled' WHERE id=?", (int(bid),))
        await bot.send_message(row[0], "К сожалению, на это время принять не получится. Выберите другое: /start")
        mark = "✖ Отказано"
    db.commit()
    await c.message.edit_text(c.message.html_text + f"\n\n<b>{mark}</b>", parse_mode="HTML")
    await c.answer("Готово")


async def schedule(m: Message, day: date):
    rows = db.execute("SELECT time, branch, opt, service, master, price, phone FROM bookings WHERE day=? AND status!='cancelled' "
                      "ORDER BY time", (day.isoformat(),)).fetchall()
    if not rows:
        return await m.answer(f"На {human_day(day.isoformat())} записей нет.")
    lines = [f"<b>{t}</b> · {details({'branch': b, 'opt': o, 'service': s, 'master': ms}).replace(chr(10), ' · ')} · {money(p)} · {ph}"
             for t, b, o, s, ms, p, ph in rows]
    await m.answer(f"📋 <b>{human_day(day.isoformat())}</b> · записей: {len(rows)}, сумма {money(sum(x[5] for x in rows))}\n\n"
                   + "\n".join(lines), parse_mode="HTML")


@dp.message(Command("today"), is_admin)
async def today(m: Message):
    await schedule(m, date.today())


@dp.message(Command("tomorrow"), is_admin)
async def tomorrow(m: Message):
    await schedule(m, date.today() + timedelta(days=1))


@dp.message(Command("all"), is_admin)
async def broadcast(m: Message, bot: Bot):
    """Рассылка всем прошлым клиентам: /all Текст сообщения"""
    text = m.text.partition(" ")[2]
    if not text:
        return await m.answer("Напишите текст после команды, например: /all В субботу есть свободные окна, записывайтесь: /start")
    users = [u for (u,) in db.execute("SELECT DISTINCT user_id FROM bookings WHERE user_id NOT IN (SELECT user_id FROM optout)")]
    sent = 0
    for uid in users:
        try:
            await bot.send_message(uid, text)
            sent += 1
        except Exception:
            pass
        await asyncio.sleep(0.1)
    await m.answer(f"Отправлено {sent} из {len(users)} клиентам.")


# ---------- напоминания и «после визита» ----------

async def loop(bot: Bot):
    while True:
        now = datetime.now()
        rows = db.execute("SELECT id, user_id, day, time, visited, followed, reminded FROM bookings WHERE status!='cancelled' "
                          "AND (reminded=0 OR visited=0 OR followed=0)").fetchall()
        for bid, uid, day, t, visited, followed, reminded in rows:
            start = datetime.fromisoformat(f"{day}T{t}")
            try:
                if not reminded and timedelta(0) < start - now <= REMIND_BEFORE and 9 <= now.hour < 22:
                    await bot.send_message(uid, f"⏰ Напоминаю: <b>{human_day(day)}, {t}</b> вас ждут в «{NAME}».\n📍 {ADDRESS}",
                                           parse_mode="HTML", reply_markup=kb([("📍 Маршрут", f"url:{MAP_URL}"), ("❌ Не смогу", f"cancel:{bid}")]))
                    db.execute("UPDATE bookings SET reminded=1 WHERE id=?", (bid,))
                if not visited and now > start + timedelta(hours=2):
                    db.execute("UPDATE bookings SET visited=1 WHERE id=?", (bid,))
                    c = active_course(uid)
                    if c:
                        db.execute("UPDATE courses SET used=used+1 WHERE id=?", (c[0],))
                        left = c[2] - c[3] - 1
                        await bot.send_message(uid, f"🎟 Сеанс {c[3] + 1} из {c[2]} пройден. " +
                                               (f"Осталось {left}. Записаться на следующий?" if left else "Курс завершён, спасибо! 🙏"),
                                               reply_markup=kb([("📅 Записаться", "go")], 1) if left else None)
                if visited and not followed and FOLLOW and now.hour >= 11:
                    due, text = follow_due(day)
                    if date.today() >= due:
                        db.execute("UPDATE bookings SET followed=1 WHERE id=?", (bid,))
                        newer = db.execute("SELECT 1 FROM bookings WHERE user_id=? AND day>? AND status!='cancelled'", (uid, day)).fetchone()
                        opted = db.execute("SELECT 1 FROM optout WHERE user_id=?", (uid,)).fetchone()
                        if not newer and not opted:
                            await bot.send_message(uid, text, reply_markup=kb([("📅 Записаться", "go"), ("🔕 Не напоминать", "optout")], 1))
            except Exception:
                pass
            db.commit()
        await asyncio.sleep(300)


def follow_due(day):
    if FOLLOW["mode"] == "season":
        when, what = next_season(day)
        return when, f"Здравствуйте! Это {NAME}. Пора менять резину на {what}. Запишитесь заранее, пока есть удобное время."
    return date.fromisoformat(day) + timedelta(days=FOLLOW["days"]), FOLLOW["text"].replace("{name}", NAME)


async def main():
    bot = Bot(BOT_TOKEN)
    await bot.set_my_commands([BotCommand(command="start", description="Записаться"),
                               BotCommand(command="my", description="Мои записи")])
    asyncio.create_task(loop(bot))
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
