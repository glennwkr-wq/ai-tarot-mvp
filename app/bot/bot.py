import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand

from app.core.config import settings
from app.bot.handlers import start, tarot

from app.db.base import Base
from app.db.session import engine
from app.models import user, reading

from app.services.user_service import check_notifications


session = AiohttpSession()

bot = Bot(
    token=settings.BOT_TOKEN,
    session=session,
)

dp = Dispatcher(storage=MemoryStorage())

dp.include_router(start.router)
dp.include_router(tarot.router)


async def set_commands():
    commands = [
        BotCommand(
            command="start",
            description="Нажми, если я перестала отвечать",
        ),
    ]
    await bot.set_my_commands(commands)


# 👇 ФОНОВАЯ ЗАДАЧА
async def notification_loop():
    while True:
        try:
            await check_notifications(bot)
        except Exception as e:
            print(f"Notification error: {e}")

        await asyncio.sleep(60)  # раз в минуту


async def main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    me = await bot.get_me()
    print(f"✅ Бот авторизован как @{me.username}")

    await set_commands()

    # 👇 запускаем фоновую задачу
    asyncio.create_task(notification_loop())

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())