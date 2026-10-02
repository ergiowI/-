"""Фикстура `bot`: настоящий Dispatcher с нашими роутерами, но вместо Telegram API — запись отправленных сообщений.

Тест пишет от имени пользователя (`bot.send(chat, "текст")`, `bot.press(chat, "callback_data")`)
и проверяет, что бот ответил (`bot.last(chat)`) и что лежит в базе (`bot.db`).
"""
import asyncio
import datetime as dt
from dataclasses import replace

import pytest
from aiogram import Bot, Dispatcher
from aiogram.types import CallbackQuery, Chat, Contact, Message, Update, User

from bot.config import load_settings
from bot.db import Database
from bot.handlers import client, owner

OWNER = 999
CLIENT = 5
OTHER = 6


class FakeBot(Bot):
    """Bot, который не ходит в сеть: складывает вызовы API в список."""

    def __init__(self):
        super().__init__("123:TEST")
        self.sent: list[dict] = []
        self.blocked: set[int] = set()  # чаты, которые «заблокировали бота»

    async def __call__(self, method, request_timeout=None):
        name = type(method).__name__
        if getattr(method, "chat_id", None) in self.blocked:
            from aiogram.exceptions import TelegramForbiddenError
            raise TelegramForbiddenError(method=method, message="Forbidden: bot was blocked by the user")
        doc = getattr(method, "document", None)
        self.sent.append({
            "document": (doc.filename, doc.data) if doc is not None and hasattr(doc, "data") else None,
            "method": name,
            "chat_id": getattr(method, "chat_id", None),
            "text": getattr(method, "text", None),
            "markup": getattr(method, "reply_markup", None),
            "alert": getattr(method, "text", None) if name == "AnswerCallbackQuery" else None,
        })
        if name in ("SendMessage", "EditMessageText"):
            return Message(message_id=1, date=dt.datetime.now(), chat=Chat(id=getattr(method, "chat_id", None) or 1, type="private"), text="x")
        return True


class Harness:
    def __init__(self, settings, db):
        self.settings, self.db = settings, db
        self.api = FakeBot()
        self.dp = Dispatcher(settings=settings, db=db)
        self.dp.include_router(owner.router)
        self.dp.include_router(client.router)
        self.loop = asyncio.new_event_loop()
        self._n = 0
        self.tz = settings.tz

    def _id(self):
        self._n += 1
        return self._n

    def _user(self, chat):
        return User(id=chat, is_bot=False, first_name=f"U{chat}")

    def send(self, chat: int, text: str | None = None, contact_phone: str | None = None):
        contact = Contact(phone_number=contact_phone, first_name="U", user_id=chat) if contact_phone else None
        m = Message(message_id=self._id(), date=dt.datetime.now(), chat=Chat(id=chat, type="private"), from_user=self._user(chat), text=text, contact=contact)
        self.loop.run_until_complete(self.dp.feed_update(self.api, Update(update_id=self._n, message=m)))

    def press(self, chat: int, data: str):
        m = Message(message_id=1, date=dt.datetime.now(), chat=Chat(id=chat, type="private"), text="x")
        q = CallbackQuery(id=str(self._id()), from_user=self._user(chat), chat_instance="c", message=m, data=data)
        self.loop.run_until_complete(self.dp.feed_update(self.api, Update(update_id=self._n, callback_query=q)))

    def run(self, coro):
        return self.loop.run_until_complete(coro)

    # --- что бот отправил ---
    def texts(self, chat: int) -> list[str]:
        return [s["text"] for s in self.api.sent if s["chat_id"] == chat and s["text"] and s["method"] != "AnswerCallbackQuery"]

    def last(self, chat: int) -> str:
        return self.texts(chat)[-1]

    def documents(self, chat: int) -> list[tuple[str, bytes]]:
        return [s["document"] for s in self.api.sent if s["chat_id"] == chat and s["document"]]

    def last_alert(self) -> str | None:
        alerts = [s["alert"] for s in self.api.sent if s["method"] == "AnswerCallbackQuery"]
        return alerts[-1] if alerts else None

    def buttons(self, chat: int) -> list[str]:
        """callback_data кнопок последнего сообщения с inline-клавиатурой в этом чате."""
        for s in reversed(self.api.sent):
            if s["chat_id"] == chat and s["markup"] is not None and hasattr(s["markup"], "inline_keyboard"):
                return [b.callback_data for row in s["markup"].inline_keyboard for b in row]
        return []

    # --- дата/время для записи ---
    def day(self, offset: int = 1) -> str:
        return (dt.datetime.now(self.tz).date() + dt.timedelta(days=offset)).isoformat()

    def book(self, chat: int, service="tyres_r13_16", offset=1, hhmm="1200", name="Иван", phone="+7 999 123-45-67", comment=None):
        """Полный сценарий записи нового клиента."""
        self.send(chat, "📅 Записаться")
        self.press(chat, f"svc:{service}")
        self.press(chat, f"day:{self.day(offset)}")
        self.press(chat, f"time:{hhmm}")
        if "me:yes" in self.buttons(chat):
            self.press(chat, "me:yes")
        else:
            self.send(chat, name)
            self.send(chat, phone)
        if comment:
            self.send(chat, comment)
        else:
            self.press(chat, "comment:skip")
        self.press(chat, "confirm:yes")


@pytest.fixture
def bot(tmp_path, monkeypatch):
    yield from _make_bot(tmp_path, monkeypatch)


@pytest.fixture
def grooming_bot(tmp_path, monkeypatch):
    """Тот же бот с конфигом другой ниши — проверяем, что ниша меняется без правки кода."""
    monkeypatch.setenv("CONFIG_PATH", "examples/grooming.yaml")
    yield from _make_bot(tmp_path, monkeypatch)


def _make_bot(tmp_path, monkeypatch):
    monkeypatch.setenv("BOT_TOKEN", "123:TEST")
    monkeypatch.setenv("OWNER_CHAT_ID", str(OWNER))
    settings = replace(load_settings(), db_path=tmp_path / "test.db")
    h = Harness(settings, Database(settings.db_path))
    yield h
    # роутеры модульные: отцепляем их от диспетчера, чтобы следующий тест мог подключить заново
    for r in (owner.router, client.router):
        r._parent_router = None
    h.loop.close()
