import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession

from app.core.config import settings
from app.bot.handlers import start, tarot


# === ИНИЦИАЛИЗАЦИЯ КАК В РАБОЧЕМ БОТЕ ===
session = AiohttpSession()

bot = Bot(
    token=settings.BOT_TOKEN,
    session=session,
)

dp = Dispatcher()

dp.include_router(start.router)
dp.include_router(tarot.router)


async def main():
    me = await bot.get_me()
    print(f"✅ Бот авторизован как @{me.username}")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())