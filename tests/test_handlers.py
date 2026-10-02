"""Сценарии целиком: сообщения проходят через настоящие обработчики aiogram, Telegram подменён."""
import datetime as dt
import sqlite3

from bot.reminders import run_once

from .conftest import CLIENT, OTHER, OWNER


def shift_to_past(bot, booking_id, days=3):
    """Сдвигаем запись в прошлое (как будто визит уже был)."""
    con = sqlite3.connect(bot.db.path)
    con.execute("UPDATE bookings SET start_ts=start_ts-?, end_ts=end_ts-? WHERE id=?", (days * 86400, days * 86400, booking_id))
    con.commit()
    con.close()


# ---------- клиент: запись ----------

def test_start_shows_business_name(bot):
    bot.send(CLIENT, "/start")
    assert "Шиномонтаж на Ветеранов" in bot.last(CLIENT)


def test_full_booking_flow(bot):
    bot.book(CLIENT, comment="Kia Rio 185/65 R15")
    b = bot.db.get(1)
    assert b.status == "pending" and b.name == "Иван" and b.comment == "Kia Rio 185/65 R15"
    assert "Заявка отправлена" in bot.last(CLIENT)
    assert "Новая запись" in bot.last(OWNER) and "Kia Rio" in bot.last(OWNER) and "+7 999 123-45-67" in bot.last(OWNER)
    assert bot.buttons(OWNER) == ["own:ok:1", "own:no:1"]


def test_summary_shown_before_confirmation(bot):
    bot.send(CLIENT, "📅 Записаться")
    bot.press(CLIENT, "svc:balancing")
    bot.press(CLIENT, f"day:{bot.day()}")
    bot.press(CLIENT, "time:1200")
    bot.send(CLIENT, "Иван")
    bot.send(CLIENT, contact_phone="79991234567")
    bot.send(CLIENT, "Toyota Camry R17")
    summary = bot.last(CLIENT)
    assert "Проверьте запись" in summary and "Балансировка" in summary and "12:00" in summary
    assert "+79991234567" in summary  # «+» добавлен к номеру из контакта
    assert bot.db.get(1) is None  # до подтверждения ничего не записано


def test_short_name_and_bad_phone_rejected(bot):
    bot.send(CLIENT, "📅 Записаться")
    bot.press(CLIENT, "svc:balancing")
    bot.press(CLIENT, f"day:{bot.day()}")
    bot.press(CLIENT, "time:1200")
    bot.send(CLIENT, "И")
    assert "минимум 2 символа" in bot.last(CLIENT)
    bot.send(CLIENT, "Иван")
    bot.send(CLIENT, "123")
    assert "Не похоже на номер" in bot.last(CLIENT)


def test_client_cancels_before_confirm(bot):
    bot.send(CLIENT, "📅 Записаться")
    bot.press(CLIENT, "svc:balancing")
    bot.press(CLIENT, f"day:{bot.day()}")
    bot.press(CLIENT, "time:1200")
    bot.send(CLIENT, "Иван")
    bot.send(CLIENT, "+7 999 123-45-67")
    bot.press(CLIENT, "comment:skip")
    bot.press(CLIENT, "confirm:no")
    assert bot.db.get(1) is None


def test_busy_slot_not_offered(bot):
    bot.book(OTHER, service="tyres_r13_16", hhmm="1200")  # 12:00–13:00 занято
    bot.send(CLIENT, "📅 Записаться")
    bot.press(CLIENT, "svc:tyres_r13_16")
    bot.press(CLIENT, f"day:{bot.day()}")
    offered = bot.buttons(CLIENT)
    assert "time:1100" in offered and "time:1300" in offered
    assert not {"time:1130", "time:1200", "time:1230"} & set(offered)


def test_two_clients_same_time_only_one_wins(bot):
    # оба дошли до подтверждения на одно и то же время
    for chat in (CLIENT, OTHER):
        bot.send(chat, "📅 Записаться")
        bot.press(chat, "svc:tyres_r13_16")
        bot.press(chat, f"day:{bot.day()}")
        bot.press(chat, "time:1200")
        bot.send(chat, "Клиент")
        bot.send(chat, "+7 999 000-00-00")
        bot.press(chat, "comment:skip")
    bot.press(CLIENT, "confirm:yes")
    bot.press(OTHER, "confirm:yes")
    assert bot.db.get(1).chat_id == CLIENT
    assert bot.db.get(2) is None
    assert "только что заняли" in bot.last(OTHER)


def test_returning_client_not_asked_again(bot):
    bot.book(CLIENT, hhmm="1000")
    bot.send(CLIENT, "📅 Записаться")
    bot.press(CLIENT, "svc:balancing")
    bot.press(CLIENT, f"day:{bot.day()}")
    bot.press(CLIENT, "time:1500")
    assert "Записать вас как Иван" in bot.last(CLIENT)
    bot.press(CLIENT, "me:yes")
    bot.press(CLIENT, "comment:skip")
    bot.press(CLIENT, "confirm:yes")
    assert bot.db.get(2).name == "Иван"


def test_unknown_text_gets_menu_hint(bot):
    bot.send(CLIENT, "привет")
    assert "кнопками меню" in bot.last(CLIENT)


# ---------- владелец ----------

def test_owner_confirms_and_client_notified(bot):
    bot.book(CLIENT)
    bot.press(OWNER, "own:ok:1")
    assert bot.db.get(1).status == "confirmed"
    assert "подтверждена" in bot.last(CLIENT)


def test_owner_cancels_and_slot_is_free_again(bot):
    bot.book(CLIENT, hhmm="1200")
    bot.press(OWNER, "own:no:1")
    assert bot.db.get(1).status == "cancelled"
    assert "запись отменена" in bot.last(CLIENT)
    bot.book(OTHER, hhmm="1200")
    assert bot.db.get(2) is not None


def test_client_cannot_use_owner_buttons_or_commands(bot):
    bot.book(CLIENT)
    bot.press(CLIENT, "own:ok:1")
    assert bot.db.get(1).status == "pending"
    bot.send(CLIENT, "/today")
    assert "кнопками меню" in bot.last(CLIENT)


def test_today_and_week(bot):
    bot.book(CLIENT, offset=1, hhmm="1200")
    bot.send(OWNER, "/today")
    assert "записей нет" in bot.last(OWNER)
    bot.send(OWNER, "/week")
    assert "12:00" in bot.last(OWNER) and "Иван" in bot.last(OWNER)


def test_stats(bot):
    bot.book(CLIENT, offset=1, hhmm="1000")
    bot.press(OWNER, "own:ok:1")
    shift_to_past(bot, 1)
    bot.press(CLIENT, "rate:1:4")
    bot.book(OTHER, offset=2, hhmm="1200")  # будущая, ждёт подтверждения
    bot.send(OWNER, "/stats")
    s = bot.last(OWNER)
    assert "Визитов: 1" in s and "2 400 ₽" in s and "4.0" in s and "ждут подтверждения: 1" in s


# ---------- «Мои записи»: отмена и перенос ----------

def test_my_bookings_and_cancel(bot):
    bot.book(CLIENT)
    bot.send(CLIENT, "📋 Мои записи")
    assert bot.buttons(CLIENT) == ["move:1", "cancel:1"]
    bot.press(CLIENT, "cancel:1")
    assert bot.db.get(1).status == "cancelled"
    assert "Клиент отменил запись" in bot.last(OWNER)


def test_cannot_cancel_someone_elses_booking(bot):
    bot.book(CLIENT)
    bot.press(OTHER, "cancel:1")
    assert bot.db.get(1).status == "pending"
    assert bot.last_alert() == "Запись не найдена"


def test_reschedule(bot):
    bot.book(CLIENT, offset=1, hhmm="1200")
    bot.press(OWNER, "own:ok:1")
    bot.press(CLIENT, "move:1")
    bot.press(CLIENT, f"mday:{bot.day(2)}")
    bot.press(CLIENT, "mtime:1500")
    b = bot.db.get(1)
    assert b.start.astimezone(bot.tz).strftime("%H:%M") == "15:00"
    assert b.status == "pending"  # после переноса владелец подтверждает заново
    assert "Перенос записи" in bot.last(OWNER) and "Было" in bot.last(OWNER)


def test_reschedule_to_busy_time_refused(bot):
    bot.book(OTHER, offset=2, hhmm="1500", name="Пётр")
    bot.book(CLIENT, offset=1, hhmm="1200")
    bot.press(CLIENT, "move:2")
    bot.press(CLIENT, f"mday:{bot.day(2)}")
    assert "mtime:1500" not in bot.buttons(CLIENT)  # занятое время не предлагается
    bot.press(CLIENT, "mtime:1500")  # даже если нажать устаревшую кнопку
    assert bot.db.get(2).start.astimezone(bot.tz).strftime("%H:%M") == "12:00"
    assert "заняли" in bot.last_alert()


# ---------- напоминания и оценки ----------

def test_reminder_and_review_requests(bot):
    bot.book(CLIENT, offset=1, hhmm="1200")
    bot.press(OWNER, "own:ok:1")
    b = bot.db.get(1)
    bot.run(run_once(bot.api, bot.settings, bot.db, now=b.start - dt.timedelta(hours=1)))
    assert "Напоминаем" in bot.last(CLIENT)
    bot.run(run_once(bot.api, bot.settings, bot.db, now=b.start - dt.timedelta(minutes=30)))
    assert sum("Напоминаем" in t for t in bot.texts(CLIENT)) == 1  # второй раз не шлём
    bot.run(run_once(bot.api, bot.settings, bot.db, now=b.end + dt.timedelta(hours=1, minutes=1)))
    assert "Оцените" in bot.last(CLIENT)
    assert bot.buttons(CLIENT) == [f"rate:1:{i}" for i in range(1, 6)]


def test_rating_only_after_visit_and_once(bot):
    bot.book(CLIENT)
    bot.press(OWNER, "own:ok:1")
    bot.press(CLIENT, "rate:1:5")
    assert bot.db.get(1).rating is None  # визит ещё не состоялся
    shift_to_past(bot, 1)
    bot.press(CLIENT, "rate:1:2")
    assert bot.db.get(1).rating == 2
    assert "Оценка визита" in bot.last(OWNER)
    assert "Управляющий свяжется" in bot.last(CLIENT)  # низкая оценка — обещаем перезвонить
    bot.press(CLIENT, "rate:1:5")
    assert bot.db.get(1).rating == 2


# ---------- другая ниша из examples/ ----------

def test_grooming_config_full_flow(grooming_bot):
    b = grooming_bot
    b.send(CLIENT, "/start")
    assert "Пушистый хвост" in b.last(CLIENT)
    b.send(CLIENT, "📅 Записаться")
    assert "svc:full_small" in b.buttons(CLIENT)
    b.press(CLIENT, "svc:full_small")
    days = [x.split(":", 1)[1] for x in b.buttons(CLIENT) if x.startswith("day:")]
    assert days and all(dt.date.fromisoformat(d).weekday() != 0 for d in days)  # понедельник — выходной
    b.press(CLIENT, f"day:{days[0]}")
    b.press(CLIENT, b.buttons(CLIENT)[0])
    b.send(CLIENT, "Анна")
    b.send(CLIENT, "+7 999 555-44-33")
    assert "породу и кличку" in b.last(CLIENT)
    b.send(CLIENT, "шпиц Боня")
    assert "🐾 шпиц Боня" in b.last(CLIENT)
    b.press(CLIENT, "confirm:yes")
    booking = b.db.get(1)
    assert booking.service_id == "full_small" and (booking.end - booking.start) == dt.timedelta(minutes=120)
    assert "2800 ₽" in b.last(OWNER)


# ---------- рассылка, выгрузка, лимит записей ----------

def test_broadcast_preview_then_send_with_unsubscribe(bot):
    bot.book(CLIENT, hhmm="1000")
    bot.book(OTHER, hhmm="1200", name="Пётр")
    bot.send(OWNER, "/broadcast Скоро снег! Есть окна во вторник.")
    assert "Предпросмотр" in bot.last(OWNER)
    assert bot.buttons(OWNER) == ["bc:send", "bc:cancel"]
    assert "Скоро снег" not in bot.last(CLIENT)  # до подтверждения ничего не ушло
    bot.press(OWNER, "bc:send")
    assert bot.last(CLIENT) == "Скоро снег! Есть окна во вторник."
    assert bot.buttons(CLIENT) == ["unsub"]
    assert "Рассылка отправлена: 2" in bot.last(OWNER)
    # повторное нажатие не шлёт второй раз
    bot.press(OWNER, "bc:send")
    assert sum("Скоро снег" in t for t in bot.texts(CLIENT)) == 1


def test_broadcast_cancel_and_empty(bot):
    bot.send(OWNER, "/broadcast Привет")
    assert "некому отправлять" in bot.last(OWNER)
    bot.book(CLIENT)
    bot.send(OWNER, "/broadcast")
    assert "Напишите текст после команды" in bot.last(OWNER)
    bot.send(OWNER, "/broadcast Акция")
    bot.press(OWNER, "bc:cancel")
    assert "Рассылка отменена" in bot.last(OWNER)
    assert "Акция" not in bot.texts(CLIENT)


def test_unsubscribed_and_blocked_clients(bot):
    bot.book(CLIENT, hhmm="1000")
    bot.book(OTHER, hhmm="1200", name="Пётр")
    bot.book(7, hhmm="1500", name="Ира")
    bot.press(CLIENT, "unsub")
    bot.api.blocked.add(7)
    bot.send(OWNER, "/broadcast Новость")
    assert "📤 Отправить 2 клиентам" in [b.text for row in bot.api.sent[-1]["markup"].inline_keyboard for b in row]
    bot.press(OWNER, "bc:send")
    assert "Новость" not in bot.texts(CLIENT)  # отписался
    assert bot.last(OTHER) == "Новость"
    assert "Рассылка отправлена: 1" in bot.last(OWNER) and "Не доставлено: 1" in bot.last(OWNER)


def test_client_cannot_broadcast_or_export(bot):
    bot.book(CLIENT)
    bot.send(CLIENT, "/broadcast спам")
    bot.send(CLIENT, "/export")
    assert "спам" not in bot.texts(OTHER)
    assert bot.documents(CLIENT) == []


def test_export_csv(bot):
    bot.book(CLIENT, hhmm="1000", comment="Kia Rio; R15")  # «;» внутри поля не ломает CSV
    bot.press(OWNER, "own:ok:1")
    bot.book(OTHER, hhmm="1200", name="Пётр")
    bot.press(OWNER, "own:no:2")
    bot.send(OWNER, "/export")
    name, data = bot.documents(OWNER)[-1]
    assert name.startswith("zapisi_") and name.endswith(".csv")
    assert data.startswith(b"\xef\xbb\xbf")  # BOM для Excel
    import csv, io
    rows = list(csv.reader(io.StringIO(data.decode("utf-8-sig")), delimiter=";"))
    assert rows[0][:4] == ["№", "Дата", "Время", "Услуга"]
    assert rows[1][3] == "Переобувка R13–R16" and rows[1][4] == "2400" and rows[1][7] == "Kia Rio; R15" and rows[1][8] == "подтверждена"
    assert rows[2][5] == "Пётр" and rows[2][8] == "отменена"
    assert len(rows) == 3


def test_export_empty(bot):
    bot.send(OWNER, "/export")
    assert "выгружать нечего" in bot.last(OWNER)


def test_active_bookings_limit(bot):
    bot.book(CLIENT, hhmm="1000")
    bot.book(CLIENT, hhmm="1200")
    bot.send(CLIENT, "📅 Записаться")
    assert "это максимум" in bot.last(CLIENT)
    bot.press(CLIENT, "cancel:1")
    bot.send(CLIENT, "📅 Записаться")
    assert bot.last(CLIENT) == "Выберите услугу:"
