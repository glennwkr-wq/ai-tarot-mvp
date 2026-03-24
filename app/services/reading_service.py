import json

from app.db.session import SessionLocal
from app.models.reading import Reading
from app.services.user_service import get_user


async def save_reading(telegram_id: int, question: str, cards: list, answer: str):
    user = await get_user(telegram_id)

    if not user:
        return  # защита

    async with SessionLocal() as session:
        reading = Reading(
            user_id=user.id,  # 🔥 ВАЖНО: используем ID из БД
            question=question,
            cards=json.dumps(cards),
            answer=answer
        )
        session.add(reading)
        await session.commit()