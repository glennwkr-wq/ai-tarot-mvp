from sqlalchemy import select, update

from app.db.session import SessionLocal
from app.models.user import User
from app.core.config import settings


async def get_user(telegram_id: int):
    async with SessionLocal() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()


async def create_user(telegram_id: int, name: str, birthdate: str, zodiac: str):
    async with SessionLocal() as session:
        user = User(
            telegram_id=telegram_id,
            name=name,
            birthdate=birthdate,
            zodiac=zodiac,
            balance=10
        )
        session.add(user)
        await session.commit()
        return user


async def update_user_name(telegram_id: int, new_name: str):
    async with SessionLocal() as session:
        await session.execute(
            update(User)
            .where(User.telegram_id == telegram_id)
            .values(name=new_name)
        )
        await session.commit()


async def update_user_birthdate(telegram_id: int, new_birthdate: str, new_zodiac: str):
    async with SessionLocal() as session:
        await session.execute(
            update(User)
            .where(User.telegram_id == telegram_id)
            .values(
                birthdate=new_birthdate,
                zodiac=new_zodiac
            )
        )
        await session.commit()


# ===== БАЛАНС =====

async def get_balance(telegram_id: int) -> int:
    if telegram_id == settings.ADMIN_ID:
        return 9999

    user = await get_user(telegram_id)
    return user.balance if user else 0


async def change_balance(telegram_id: int, amount: int):
    if telegram_id == settings.ADMIN_ID:
        return

    async with SessionLocal() as session:
        await session.execute(
            update(User)
            .where(User.telegram_id == telegram_id)
            .values(balance=User.balance + amount)
        )
        await session.commit()


# ===== ОТОБРАЖЕНИЕ ПРОФИЛЯ =====

async def get_display_balance(user: User) -> int:
    if user.telegram_id == settings.ADMIN_ID:
        return 9999
    return user.balance