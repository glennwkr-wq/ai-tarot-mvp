from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.user import User


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