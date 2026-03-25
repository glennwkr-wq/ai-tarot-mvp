from datetime import datetime
from sqlalchemy import select, update

from app.db.session import SessionLocal
from app.models.user import User
from app.core.config import settings


def is_admin(telegram_id: int) -> bool:
    return telegram_id in settings.admin_ids


async def get_user(telegram_id: int):
    async with SessionLocal() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()

        if user and not is_admin(telegram_id):
            await apply_daily_bonus_if_needed(user)

        return user


async def create_user(telegram_id: int, name: str, birthdate: str, zodiac: str):
    async with SessionLocal() as session:
        user = User(
            telegram_id=telegram_id,
            name=name,
            birthdate=birthdate,
            zodiac=zodiac,
            balance=30,
            last_daily_bonus=datetime.utcnow(),
            last_card_of_day=None,
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


# ===== ЕЖЕДНЕВНЫЙ БОНУС =====

async def apply_daily_bonus_if_needed(user: User):
    now = datetime.utcnow()

    if user.last_daily_bonus is None or user.last_daily_bonus.date() != now.date():
        async with SessionLocal() as session:
            await session.execute(
                update(User)
                .where(User.telegram_id == user.telegram_id)
                .values(
                    balance=User.balance + 10,
                    last_daily_bonus=now
                )
            )
            await session.commit()

        user.balance += 10
        user.last_daily_bonus = now


# ===== УВЕДОМЛЕНИЯ =====

async def check_notifications(bot):
    async with SessionLocal() as session:
        result = await session.execute(select(User))
        users = result.scalars().all()

        now = datetime.utcnow()

        for user in users:
            # ===== БОНУС =====
            bonus_available = (
                user.last_daily_bonus is None
                or user.last_daily_bonus.date() != now.date()
            )

            if bonus_available:
                if (
                    user.last_bonus_notified is None
                    or user.last_bonus_notified.date() != now.date()
                ):
                    try:
                        await bot.send_message(
                            user.telegram_id,
                            "✨ Для вас открыт новый поток энергии.\n\n"
                            "💰 Начислено +10 кредитов."
                        )
                    except Exception:
                        continue

                    await session.execute(
                        update(User)
                        .where(User.telegram_id == user.telegram_id)
                        .values(last_bonus_notified=now)
                    )

            # ===== КАРТА ДНЯ =====
            card_available = (
                user.last_card_of_day is None
                or user.last_card_of_day.date() != now.date()
            )

            if card_available:
                if (
                    user.last_card_notified is None
                    or user.last_card_notified.date() != now.date()
                ):
                    try:
                        await bot.send_message(
                            user.telegram_id,
                            "🃏 Карта дня снова открыта для вас.\n\n"
                            "Она уже ждёт✨."
                        )
                    except Exception:
                        continue

                    await session.execute(
                        update(User)
                        .where(User.telegram_id == user.telegram_id)
                        .values(last_card_notified=now)
                    )

        await session.commit()


# ===== БАЛАНС =====

async def get_balance(telegram_id: int) -> int:
    if is_admin(telegram_id):
        return 9999

    user = await get_user(telegram_id)
    return user.balance if user else 0


async def change_balance(telegram_id: int, amount: int):
    if is_admin(telegram_id):
        return

    async with SessionLocal() as session:
        await session.execute(
            update(User)
            .where(User.telegram_id == telegram_id)
            .values(balance=User.balance + amount)
        )
        await session.commit()


# ===== КАРТА ДНЯ =====

async def can_use_free_card_today(user: User) -> bool:
    now = datetime.utcnow()

    if user.last_card_of_day is None:
        return True

    return user.last_card_of_day.date() != now.date()


async def mark_card_of_day_used(telegram_id: int):
    async with SessionLocal() as session:
        await session.execute(
            update(User)
            .where(User.telegram_id == telegram_id)
            .values(last_card_of_day=datetime.utcnow())
        )
        await session.commit()


# ===== ОТОБРАЖЕНИЕ ПРОФИЛЯ =====

async def get_display_balance(user: User) -> int:
    if is_admin(user.telegram_id):
        return 9999
    return user.balance