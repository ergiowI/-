import asyncio
import logging

from aiogram import Bot, Dispatcher

from .config import load_settings
from .db import Database
from .handlers import client, owner
from .reminders import reminder_loop


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    settings = load_settings()
    db = Database(settings.db_path)
    bot = Bot(settings.bot_token)
    dp = Dispatcher(settings=settings, db=db)
    dp.include_router(owner.router)  # владелец первым: его команды и кнопки
    dp.include_router(client.router)
    task = asyncio.create_task(reminder_loop(bot, settings, db))
    try:
        await dp.start_polling(bot)
    finally:
        task.cancel()


if __name__ == "__main__":
    asyncio.run(main())
