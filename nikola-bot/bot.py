"""Telegram-бот «Шиномонтаж и эвакуация Никола»: запись на шиномонтаж с ценой + вызов эвакуатора по геопозиции.

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
from math import asin, cos, radians, sin, sqrt
from urllib.parse import quote

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (BotCommand, CallbackQuery, FSInputFile, InlineKeyboardButton, InlineKeyboardMarkup,
                           KeyboardButton, Message, ReplyKeyboardMarkup, ReplyKeyboardRemove, WebAppInfo)

BOT_TOKEN = os.environ["BOT_TOKEN"]
ADMIN_CHAT_ID = int(os.environ["ADMIN_CHAT_ID"])  # чат мастера: сюда приходят заявки
WEBAPP_URL = os.environ.get("WEBAPP_URL", "")      # https-адрес webapp/index.html

NAME = "Шиномонтаж и эвакуация Никола"
ADDRESS = "пр. Ветеранов, 143"
MAP_URL = "https://yandex.ru/maps/?text=" + quote("Санкт-Петербург, проспект Ветеранов, 143")
BASE = (59.8337, 30.1486)  # координаты точки, для расчёта расстояния до клиента
# Эвакуатор: подача + первые 5 км, дальше за км; внедорожник дороже; если везём к нам на шиномонтаж — скидка
EVAC_BASE, EVAC_PER_KM, EVAC_FREE_KM, EVAC_SUV, EVAC_OUR_DISCOUNT = 3500, 100, 5, 1000, 0.2
REASONS = {"wheel": "🛞 Пробито колесо", "start": "🔋 Не заводится", "dtp": "💥 ДТП", "other": "❔ Другое"}
WORK_HOURS = range(10, 21)  # слоты 10:00–20:00
SLOT_CAPACITY = 1           # сколько машин в одно время (число постов)
BANNER = Path(__file__).with_name("banner.png")

# Прайс: комплекс (снятие/установка + монтаж + балансировка), 4 колеса. Тот же, что в webapp/index.html
PRICES = {
    "car":   {"R13": 1800, "R14": 1900, "R15": 2100, "R16": 2400, "R17": 2700, "R18": 3100, "R19": 3500, "R20": 3900},
    "cross": {"R15": 2500, "R16": 2800, "R17": 3100, "R18": 3500, "R19": 3900, "R20": 4400, "R21": 4900},
    "suv":   {"R16": 3200, "R17": 3600, "R18": 4000, "R19": 4500, "R20": 5000, "R21": 5600, "R22": 6200},
}
TYPES = {"car": "Легковой", "cross": "Кроссовер", "suv": "Внедорожник"}
SERVICES = {
    "full":   ("Сезонная переобувка", 1.0),
    "wheels": ("Перестановка колёс", 0.45),
    "bal":    ("Балансировка 4 колёс", 0.4),
}
EXTRAS = {"valves": ("Новые вентили", 400), "bags": ("Пакеты для шин", 200)}

WEEKDAYS = ["пн", "вт", "ср", "чт", "пт", "сб", "вс"]
MONTHS = ["января", "февраля", "марта", "апреля", "мая", "июня", "июля", "августа",
          "сентября", "октября", "ноября", "декабря"]
LINE = "━━━━━━━━━━━━━━━"

db = sqlite3.connect("bookings.db")
db.execute("""CREATE TABLE IF NOT EXISTS bookings (
    id INTEGER PRIMARY KEY, user_id INTEGER, day TEXT, time TEXT, car TEXT, radius TEXT,
    service TEXT, extras TEXT, price INTEGER, phone TEXT, status TEXT DEFAULT 'new',
    reminded INTEGER DEFAULT 0, created TEXT)""")
db.execute("""CREATE TABLE IF NOT EXISTS evac (
    id INTEGER PRIMARY KEY, user_id INTEGER, reason TEXT, car TEXT, lat REAL, lon REAL, dest TEXT,
    price INTEGER, phone TEXT, status TEXT DEFAULT 'new', created TEXT)""")
db.commit()


class Booking(StatesGroup):
    type = State()
    radius = State()
    service = State()
    extras = State()
    day = State()
    time = State()
    phone = State()


class Evac(StatesGroup):
    reason = State()
    type = State()
    location = State()
    dest = State()
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


def calc(data):
    base = PRICES[data["type"]][data["radius"]]
    svc = round(base * SERVICES[data["service"]][1] / 50) * 50
    return svc + sum(EXTRAS[e][1] for e in data.get("extras", []))


def km_to(lat, lon):
    la1, lo1, la2, lo2 = map(radians, (*BASE, lat, lon))
    h = sin((la2 - la1) / 2) ** 2 + cos(la1) * cos(la2) * sin((lo2 - lo1) / 2) ** 2
    return 2 * 6371 * asin(sqrt(h))


def evac_price(data):
    extra_km = max(0, int(km_to(data["lat"], data["lon"]) + 0.999) - EVAC_FREE_KM)
    full = EVAC_BASE + extra_km * EVAC_PER_KM + (EVAC_SUV if data["type"] == "suv" else 0)
    return round(full * (1 - EVAC_OUR_DISCOUNT) / 50) * 50 if data["dest"] == "us" else full


def eta(data):
    return max(15, round(km_to(data["lat"], data["lon"]) * 3 + 10))


def busy_count(day, time):
    return db.execute("SELECT COUNT(*) FROM bookings WHERE day=? AND time=? AND status!='cancelled'",
                      (day, time)).fetchone()[0]


def busy_slots():
    """Занятые слоты на неделю вперёд в формате 2026-10-03_11:00 для мини-приложения."""
    rows = db.execute("SELECT day, time, COUNT(*) FROM bookings WHERE status!='cancelled' AND day>=? "
                      "GROUP BY day, time", (date.today().isoformat(),)).fetchall()
    return ",".join(f"{d}_{t}" for d, t, n in rows if n >= SLOT_CAPACITY)


def my_param(user_id):
    """Будущие записи клиента для страницы «Мои записи»: 0012~2026-10-03~10:00~full~R16~car~2400,..."""
    rows = db.execute("SELECT id, day, time, service, radius, car, price FROM bookings WHERE user_id=? AND status!='cancelled' "
                      "AND day>=? ORDER BY day, time", (user_id, date.today().isoformat())).fetchall()
    return ",".join(f"{bid:04d}~{d}~{t}~{s}~{r}~{c}~{p}" for bid, d, t, s, r, c, p in rows)


def main_keyboard(user_id=None):
    """Постоянная кнопка снизу: открывает мини-приложение (sendData работает только из такой кнопки)."""
    if not WEBAPP_URL:
        return None
    sep = "&" if "?" in WEBAPP_URL else "?"
    url = f"{WEBAPP_URL}{sep}busy={busy_slots()}"
    if user_id is not None:
        url += f"&my={my_param(user_id)}"
    return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="🛞 Записаться онлайн", web_app=WebAppInfo(url=url))]],
                               resize_keyboard=True, is_persistent=True)


def receipt(bid, data, total):
    extras = "".join(f"\n➕ {EXTRAS[e][0]}" for e in data.get("extras", []))
    return (f"✅ <b>Вы записаны</b> · № {bid:04d}\n{LINE}\n"
            f"📅 <b>{human_day(data['day'])} · {data['time']}</b>\n"
            f"🚗 {TYPES[data['type']]}, {data['radius']}\n"
            f"🛞 {SERVICES[data['service']][0]}{extras}\n{LINE}\n"
            f"💰 <b>{money(total)}</b>, цена зафиксирована\n"
            f"📍 {ADDRESS}\n\n"
            f"За 2 часа до визита пришлю напоминание.")


dp = Dispatcher()


# ---------- start ----------

@dp.message(CommandStart())
async def start(m: Message, state: FSMContext):
    await state.clear()
    caption = (f"<b>{NAME}</b>\n{ADDRESS} · шиномонтаж 9:00–21:00, эвакуатор круглосуточно\n\n"
               "Запишу на шиномонтаж и сразу покажу точную цену. Сломались в дороге? Жмите «🚨 Эвакуатор» "
               "и отправьте геопозицию: водитель увидит вас на карте.")
    buttons = kb([("🚨 Вызвать эвакуатор", "evac"), ("💬 Записаться в чате", "go"), ("📋 Мои записи", "my"),
                  ("📍 Как доехать", f"url:{MAP_URL}")], 1)
    if BANNER.exists():
        await m.answer_photo(FSInputFile(BANNER), caption=caption, parse_mode="HTML", reply_markup=buttons)
    else:
        await m.answer(caption, parse_mode="HTML", reply_markup=buttons)
    if WEBAPP_URL:
        await m.answer("Нажмите «🛞 Записаться онлайн» внизу: там выбор машины, радиуса и времени с ценой на лету.",
                       reply_markup=main_keyboard(m.from_user.id))


# ---------- mini app ----------

@dp.message(F.web_app_data)
async def from_webapp(m: Message, state: FSMContext, bot: Bot):
    try:
        p = json.loads(m.web_app_data.data)
        if p.get("action") == "cancel":
            await cancel_booking(bot, int(p["no"]), m.from_user.id, m)
            return
        if p.get("action") == "evac":
            data = {"reason": p["reason"], "type": p["type"], "dest": "us" if p.get("dest") == "us" else "other",
                    "lat": float(p["lat"]), "lon": float(p["lon"])}
            REASONS[data["reason"]], TYPES[data["type"]]  # проверка значений
            await state.set_data(data)
            await evac_ask_phone(m, state)
            return
        data = {"type": p["type"], "radius": p["radius"], "service": p["service"],
                "extras": [e for e in p.get("extras", []) if e in EXTRAS], "day": p["day"], "time": p["time"]}
        PRICES[data["type"]][data["radius"]], SERVICES[data["service"]]  # проверка, что значения из прайса
        date.fromisoformat(data["day"])
    except (KeyError, ValueError, TypeError):
        await m.answer("Не получилось прочитать заявку, попробуйте ещё раз.", reply_markup=main_keyboard(m.from_user.id))
        return
    if busy_count(data["day"], data["time"]) >= SLOT_CAPACITY:
        await m.answer("Это время только что заняли 😔 Откройте запись ещё раз и выберите другое.",
                       reply_markup=main_keyboard(m.from_user.id))
        return
    await state.set_data(data)  # цену пересчитываем на сервере, не доверяем присланной
    await ask_phone(m, state)


# ---------- запись в чате ----------

@dp.callback_query(F.data == "go")
async def ask_type(c: CallbackQuery, state: FSMContext):
    await state.set_state(Booking.type)
    await c.message.answer("Шаг 1/5 · Какая у вас машина?", reply_markup=kb([(f"🚗 {v}", f"t:{k}") for k, v in TYPES.items()], 1))
    await c.answer()


@dp.callback_query(Booking.type, F.data.startswith("t:"))
async def ask_radius(c: CallbackQuery, state: FSMContext):
    t = c.data[2:]
    await state.update_data(type=t)
    await state.set_state(Booking.radius)
    await c.message.edit_text(f"Шаг 2/5 · {TYPES[t]}. Какой радиус дисков?\nОн написан на шине, например 205/55 <b>R16</b>.",
                              parse_mode="HTML", reply_markup=kb([(r, f"r:{r}") for r in PRICES[t]], 4))
    await c.answer()


@dp.callback_query(Booking.radius, F.data.startswith("r:"))
async def ask_service(c: CallbackQuery, state: FSMContext):
    await state.update_data(radius=c.data[2:])
    data = await state.get_data()
    await state.set_state(Booking.service)
    rows = [(f"{name} · {money(calc({**data, 'service': k, 'extras': []}))}", f"s:{k}") for k, (name, _) in SERVICES.items()]
    await c.message.edit_text(f"Шаг 3/5 · {TYPES[data['type']]}, {data['radius']}. Что нужно сделать?", reply_markup=kb(rows, 1))
    await c.answer()


@dp.callback_query(Booking.service, F.data.startswith("s:"))
async def ask_extras(c: CallbackQuery, state: FSMContext):
    await state.update_data(service=c.data[2:])
    await state.set_state(Booking.extras)
    await c.message.edit_text("Шаг 4/5 · Добавить что-нибудь?", reply_markup=kb([
        ("Вентили +400 ₽", "e:valves"), ("Пакеты +200 ₽", "e:bags"),
        ("Вентили и пакеты +600 ₽", "e:valves,bags"), ("Ничего не нужно", "e:")]))
    await c.answer()


@dp.callback_query(Booking.extras, F.data.startswith("e:"))
async def ask_day(c: CallbackQuery, state: FSMContext):
    await state.update_data(extras=[e for e in c.data[2:].split(",") if e])
    data = await state.get_data()
    await state.set_state(Booking.day)
    days = []
    for i in range(7):
        d = date.today() + timedelta(days=i)
        label = "Сегодня" if i == 0 else "Завтра" if i == 1 else f"{WEEKDAYS[d.weekday()]} {d.day}"
        days.append((label, f"d:{d.isoformat()}"))
    await c.message.edit_text(f"💰 Итого: <b>{money(calc(data))}</b>. Цена фиксируется при записи.\n\nШаг 5/5 · Выберите день:",
                              parse_mode="HTML", reply_markup=kb(days, 4))
    await c.answer()


@dp.callback_query(Booking.day, F.data.startswith("d:"))
async def ask_time(c: CallbackQuery, state: FSMContext):
    day = c.data[2:]
    now = datetime.now()
    free = [(f"{h:02d}:00", f"h:{h:02d}:00") for h in WORK_HOURS
            if not (day == now.date().isoformat() and h <= now.hour) and busy_count(day, f"{h:02d}:00") < SLOT_CAPACITY]
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
    await m.answer("Последний шаг: оставьте номер, чтобы мастер мог связаться, если что-то изменится.",
                   reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="📱 Отправить мой номер", request_contact=True)]],
                                                    resize_keyboard=True, one_time_keyboard=True))


@dp.message(Booking.phone)
async def finish(m: Message, state: FSMContext, bot: Bot):
    phone = m.contact.phone_number if m.contact else (m.text or "").strip()
    if len([ch for ch in phone if ch.isdigit()]) < 10:
        await m.answer("Нажмите кнопку «📱 Отправить мой номер» или напишите номер цифрами.")
        return
    data = await state.get_data()
    if busy_count(data["day"], data["time"]) >= SLOT_CAPACITY:
        await state.clear()
        await m.answer("Это время только что заняли 😔 Выберите другое: /start", reply_markup=main_keyboard(m.from_user.id))
        return
    total = calc(data)
    cur = db.execute("INSERT INTO bookings (user_id, day, time, car, radius, service, extras, price, phone, created) "
                     "VALUES (?,?,?,?,?,?,?,?,?,?)",
                     (m.from_user.id, data["day"], data["time"], data["type"], data["radius"], data["service"],
                      ",".join(data["extras"]), total, phone, datetime.now().isoformat()))
    db.commit()
    bid = cur.lastrowid
    await state.clear()
    await m.answer("Готово! 🎉", reply_markup=main_keyboard(m.from_user.id))
    await m.answer(receipt(bid, data, total), parse_mode="HTML",
                   reply_markup=kb([("📍 Маршрут", f"url:{MAP_URL}"), ("❌ Отменить", f"cancel:{bid}")]))
    extras = "".join(f"\n➕ {EXTRAS[e][0]}" for e in data["extras"])
    await bot.send_message(
        ADMIN_CHAT_ID,
        f"🛞 <b>Новая запись № {bid:04d}</b>\n{LINE}\n"
        f"📅 <b>{human_day(data['day'])} · {data['time']}</b>\n"
        f"🚗 {TYPES[data['type']]}, {data['radius']}\n🛞 {SERVICES[data['service']][0]}{extras}\n"
        f"💰 {money(total)} (клиент видел и согласен)\n📞 {phone}",
        parse_mode="HTML", reply_markup=kb([("✔ Подтвердить", f"ok:{bid}"), ("✖ Отказать", f"no:{bid}")]))


# ---------- эвакуатор ----------

@dp.message(Command("evac"))
@dp.callback_query(F.data == "evac")
async def evac_reason(event, state: FSMContext):
    m = event.message if isinstance(event, CallbackQuery) else event
    await state.clear()
    await state.set_state(Evac.reason)
    await m.answer("🚨 Вызов эвакуатора. Что случилось?", reply_markup=kb([(v, f"er:{k}") for k, v in REASONS.items()]))
    if isinstance(event, CallbackQuery):
        await event.answer()


@dp.callback_query(Evac.reason, F.data.startswith("er:"))
async def evac_type(c: CallbackQuery, state: FSMContext):
    await state.update_data(reason=c.data[3:])
    await state.set_state(Evac.type)
    await c.message.edit_text(f"{REASONS[c.data[3:]]}. Какая машина?", reply_markup=kb([(f"🚗 {v}", f"et:{k}") for k, v in TYPES.items()], 1))
    await c.answer()


@dp.callback_query(Evac.type, F.data.startswith("et:"))
async def evac_location(c: CallbackQuery, state: FSMContext):
    await state.update_data(type=c.data[3:])
    await state.set_state(Evac.location)
    await c.message.edit_reply_markup(reply_markup=None)
    await c.message.answer("Где вы? Нажмите кнопку ниже, и водитель увидит вас на карте.\n"
                           "Или пришлите точку через 📎 → Геопозиция.",
                           reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="📍 Отправить геопозицию", request_location=True)]],
                                                            resize_keyboard=True, one_time_keyboard=True))
    await c.answer()


@dp.message(Evac.location, F.location)
async def evac_dest(m: Message, state: FSMContext):
    await state.update_data(lat=m.location.latitude, lon=m.location.longitude)
    await state.set_state(Evac.dest)
    data = await state.get_data()
    dist = f"{km_to(data['lat'], data['lon']):.1f}".replace(".", ",")
    await m.answer(f"Вижу вас: ≈ {dist} км от нас, приедем примерно за {eta(data)} мин.",
                   reply_markup=main_keyboard(m.from_user.id) or ReplyKeyboardRemove())
    await m.answer("Куда везти машину?", reply_markup=kb([
        (f"🛞 К вам на шиномонтаж · ~{money(evac_price({**data, 'dest': 'us'}))}", "ed:us"),
        (f"Другой адрес · ~{money(evac_price({**data, 'dest': 'other'}))}", "ed:other")], 1))


@dp.message(Evac.location)
async def evac_need_location(m: Message):
    await m.answer("Нажмите «📍 Отправить геопозицию», чтобы водитель нашёл вас по карте. "
                   "Если кнопки нет: 📎 → Геопозиция.")


@dp.callback_query(Evac.dest, F.data.startswith("ed:"))
async def evac_dest_picked(c: CallbackQuery, state: FSMContext):
    await state.update_data(dest=c.data[3:])
    await c.message.edit_reply_markup(reply_markup=None)
    await evac_ask_phone(c.message, state)
    await c.answer()


async def evac_ask_phone(m: Message, state: FSMContext):
    await state.set_state(Evac.phone)
    await m.answer("Оставьте номер: водитель перезвонит в течение 5 минут и назовёт точную цену.",
                   reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="📱 Отправить мой номер", request_contact=True)]],
                                                    resize_keyboard=True, one_time_keyboard=True))


@dp.message(Evac.phone)
async def evac_finish(m: Message, state: FSMContext, bot: Bot):
    phone = m.contact.phone_number if m.contact else (m.text or "").strip()
    if len([ch for ch in phone if ch.isdigit()]) < 10:
        await m.answer("Нажмите кнопку «📱 Отправить мой номер» или напишите номер цифрами.")
        return
    data = await state.get_data()
    price = evac_price(data)
    cur = db.execute("INSERT INTO evac (user_id, reason, car, lat, lon, dest, price, phone, created) VALUES (?,?,?,?,?,?,?,?,?)",
                     (m.from_user.id, data["reason"], data["type"], data["lat"], data["lon"], data["dest"], price, phone,
                      datetime.now().isoformat()))
    db.commit()
    eid = cur.lastrowid
    await state.clear()
    await m.answer(f"🚨 <b>Заявка № {eid:04d} у водителя</b>\n{LINE}\n{REASONS[data['reason']]} · {TYPES[data['type']]}\n"
                   f"➡ {'к нам на шиномонтаж' if data['dest'] == 'us' else 'другой адрес, скажете водителю'}\n"
                   f"💰 примерно {money(price)}\n\nВодитель перезвонит в течение 5 минут. Оставайтесь на месте 🙏",
                   parse_mode="HTML", reply_markup=main_keyboard(m.from_user.id) or ReplyKeyboardRemove())
    dist = f"{km_to(data['lat'], data['lon']):.1f}".replace(".", ",")
    point = f"https://yandex.ru/maps/?pt={data['lon']},{data['lat']}&z=16&l=map"
    await bot.send_message(
        ADMIN_CHAT_ID,
        f"🚨 <b>ВЫЗОВ ЭВАКУАТОРА № {eid:04d}</b>\n{LINE}\n{REASONS[data['reason']]} · {TYPES[data['type']]}\n"
        f"📍 ≈ {dist} км от вас\n"
        f"➡ {'везти к нам на шиномонтаж' if data['dest'] == 'us' else 'другой адрес, уточнить'}\n"
        f"💰 примерно {money(price)}\n📞 {phone}",
        parse_mode="HTML",
        reply_markup=kb([("🚚 Выезжаю", f"ego:{eid}"), ("📞 Перезвоню", f"ecall:{eid}"), ("🗺 Открыть в Яндекс Картах", f"url:{point}")]))
    await bot.send_location(ADMIN_CHAT_ID, data["lat"], data["lon"])


@dp.callback_query(F.data.regexp(r"^(ego|ecall):\d+$"))
async def evac_admin(c: CallbackQuery, bot: Bot):
    if c.message.chat.id != ADMIN_CHAT_ID:
        return await c.answer()
    action, eid = c.data.split(":")
    row = db.execute("SELECT user_id, lat, lon, car FROM evac WHERE id=?", (int(eid),)).fetchone()
    if not row:
        return await c.answer("Заявка не найдена")
    if action == "ego":
        db.execute("UPDATE evac SET status='going' WHERE id=?", (int(eid),))
        minutes = eta({"lat": row[1], "lon": row[2]})
        await bot.send_message(row[0], f"🚚 Водитель выехал, будет примерно через {minutes} мин.")
        mark = "🚚 Выехали"
    else:
        await bot.send_message(row[0], "📞 Водитель сейчас вам перезвонит.")
        mark = "📞 Клиенту сказали, что перезвоните"
    db.commit()
    await c.message.edit_text(c.message.html_text + f"\n\n<b>{mark}</b>", parse_mode="HTML",
                              reply_markup=kb([("🚚 Выезжаю", f"ego:{eid}")]) if action == "ecall" else None)
    await c.answer("Готово")


# ---------- мои записи / отмена ----------

@dp.message(Command("my"))
@dp.callback_query(F.data == "my")
async def my_bookings(event):
    m = event.message if isinstance(event, CallbackQuery) else event
    rows = db.execute("SELECT id, day, time, service, price FROM bookings WHERE user_id=? AND status!='cancelled' "
                      "AND day>=? ORDER BY day, time", (event.from_user.id, date.today().isoformat())).fetchall()
    if not rows:
        await m.answer("Активных записей нет. Записаться: /start")
    for bid, day, t, svc, price in rows:
        await m.answer(f"№ {bid:04d} · <b>{human_day(day)}, {t}</b>\n{SERVICES[svc][0]} · {money(price)}",
                       parse_mode="HTML", reply_markup=kb([("❌ Отменить", f"cancel:{bid}")]))
    if isinstance(event, CallbackQuery):
        await event.answer()


async def cancel_booking(bot: Bot, bid: int, user_id: int, m: Message):
    row = db.execute("SELECT day, time FROM bookings WHERE id=? AND user_id=? AND status!='cancelled'",
                     (bid, user_id)).fetchone()
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


# ---------- для мастера ----------

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
        await bot.send_message(row[0], f"👍 Мастер подтвердил запись: {human_day(row[1])}, {row[2]}. Ждём вас!")
        mark = "✔ Подтверждено"
    else:
        db.execute("UPDATE bookings SET status='cancelled' WHERE id=?", (int(bid),))
        await bot.send_message(row[0], "К сожалению, на это время принять не получится. Выберите другое: /start")
        mark = "✖ Отказано"
    db.commit()
    await c.message.edit_text(c.message.html_text + f"\n\n<b>{mark}</b>", parse_mode="HTML")
    await c.answer("Готово")


async def schedule(m: Message, day: date):
    rows = db.execute("SELECT time, car, radius, service, price, phone FROM bookings WHERE day=? AND status!='cancelled' "
                      "ORDER BY time", (day.isoformat(),)).fetchall()
    if not rows:
        return await m.answer(f"На {human_day(day.isoformat())} записей нет.")
    lines = [f"<b>{t}</b> · {TYPES[car]} {r} · {SERVICES[s][0]} · {money(p)} · {ph}" for t, car, r, s, p, ph in rows]
    await m.answer(f"📋 <b>{human_day(day.isoformat())}</b> · машин: {len(rows)}, сумма {money(sum(x[4] for x in rows))}\n\n" + "\n".join(lines),
                   parse_mode="HTML")


@dp.message(Command("today"), is_admin)
async def today(m: Message):
    await schedule(m, date.today())


@dp.message(Command("tomorrow"), is_admin)
async def tomorrow(m: Message):
    await schedule(m, date.today() + timedelta(days=1))


@dp.message(Command("spring"), is_admin)
async def spring(m: Message, bot: Bot):
    """Рассылка всем прошлым клиентам: «пора переобуваться». Текст можно передать после команды."""
    text = m.text.partition(" ")[2] or ("🌱 Весна! Пора менять шины на летние.\n"
                                        "Запишитесь заранее, пока есть удобное время: /start")
    users = [u for (u,) in db.execute("SELECT DISTINCT user_id FROM bookings").fetchall()]
    sent = 0
    for uid in users:
        try:
            await bot.send_message(uid, text)
            sent += 1
        except Exception:
            pass
        await asyncio.sleep(0.1)
    await m.answer(f"Отправлено {sent} из {len(users)} клиентам.")


# ---------- напоминания ----------

async def reminders(bot: Bot):
    """Раз в 5 минут напоминает клиентам за 2 часа до визита."""
    while True:
        now = datetime.now()
        rows = db.execute("SELECT id, user_id, day, time FROM bookings WHERE status!='cancelled' AND reminded=0").fetchall()
        for bid, uid, day, t in rows:
            if timedelta(0) < datetime.fromisoformat(f"{day}T{t}") - now <= timedelta(hours=2):
                try:
                    await bot.send_message(uid, f"⏰ Напоминаю: сегодня в <b>{t}</b> вы записаны на шиномонтаж.\n📍 {ADDRESS}",
                                           parse_mode="HTML",
                                           reply_markup=kb([("📍 Маршрут", f"url:{MAP_URL}"), ("❌ Не смогу", f"cancel:{bid}")]))
                except Exception:
                    pass
                db.execute("UPDATE bookings SET reminded=1 WHERE id=?", (bid,))
                db.commit()
        await asyncio.sleep(300)


async def main():
    bot = Bot(BOT_TOKEN)
    await bot.set_my_commands([BotCommand(command="start", description="Записаться"),
                               BotCommand(command="evac", description="Вызвать эвакуатор"),
                               BotCommand(command="my", description="Мои записи")])
    asyncio.create_task(reminders(bot))
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
