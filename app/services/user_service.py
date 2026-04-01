from datetime import datetime, timedelta
from sqlalchemy import select, update, desc

from app.db.session import SessionLocal
from app.models.user import User
from app.models.reading import Reading
from app.core.config import settings


def is_admin(telegram_id: int) -> bool:
    return telegram_id in settings.admin_ids


def has_24_hours_passed(last_time: datetime | None) -> bool:
    if last_time is None:
        return False
    return datetime.utcnow() >= last_time + timedelta(hours=24)


async def get_latest_reading(user_id: int):
    async with SessionLocal() as session:
        result = await session.execute(
            select(Reading)
            .where(Reading.user_id == user_id)
            .order_by(desc(Reading.created_at))
            .limit(1)
        )
        return result.scalar_one_or_none()


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
    latest_reading = await get_latest_reading(user.id)

    if latest_reading is None:
        return

    reading_time = latest_reading.created_at

    bonus_already_given_for_this_reading = (
        user.last_daily_bonus is not None
        and user.last_daily_bonus >= reading_time
    )

    if has_24_hours_passed(reading_time) and not bonus_already_given_for_this_reading:
        now = datetime.utcnow()

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
            if is_admin(user.telegram_id):
                continue

            # ===== БОНУС =====
            latest_reading_result = await session.execute(
                select(Reading)
                .where(Reading.user_id == user.id)
                .order_by(desc(Reading.created_at))
                .limit(1)
            )
            latest_reading = latest_reading_result.scalar_one_or_none()

            if latest_reading is not None:
                reading_time = latest_reading.created_at

                bonus_already_given_for_this_reading = (
                    user.last_daily_bonus is not None
                    and user.last_daily_bonus >= reading_time
                )

                bonus_already_notified_for_this_reading = (
                    user.last_bonus_notified is not None
                    and user.last_bonus_notified >= reading_time
                )

                bonus_available = (
                    has_24_hours_passed(reading_time)
                    and not bonus_already_given_for_this_reading
                )

                if bonus_available and not bonus_already_notified_for_this_reading:
                    try:
                        await bot.send_message(
                            user.telegram_id,
                            "✨ Для вас снова открыт поток энергии.\n\n"
                            "💰 Начислено +10 монет."
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
                user.last_card_of_day is not None
                and has_24_hours_passed(user.last_card_of_day)
            )

            card_already_notified_for_this_cycle = (
                user.last_card_notified is not None
                and user.last_card_of_day is not None
                and user.last_card_notified >= user.last_card_of_day
            )

            if card_available and not card_already_notified_for_this_cycle:
                try:
                    await bot.send_message(
                        user.telegram_id,
                        "🃏 Бесплатная карта дня снова доступна.\n\n"
                        "Она уже ждёт тебя ✨"
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
    if user.last_card_of_day is None:
        return True

    return has_24_hours_passed(user.last_card_of_day)


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