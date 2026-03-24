import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.fsm.storage.memory import MemoryStorage

from app.core.config import settings
from app.bot.handlers import start, tarot

from app.db.base import Base
from app.db.session import engine
from app.models import user, reading


session = AiohttpSession()

bot = Bot(
    token=settings.BOT_TOKEN,
    session=session,
)

dp = Dispatcher(storage=MemoryStorage())

# ❗ УБРАЛИ menu.router
dp.include_router(start.router)
dp.include_router(tarot.router)


async def main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    me = await bot.get_me()
    print(f"✅ Бот авторизован как @{me.username}")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())