import json

from app.db.session import SessionLocal
from app.models.reading import Reading


async def save_reading(user_id: int, question: str, cards: list, answer: str):
    async with SessionLocal() as session:
        reading = Reading(
            user_id=user_id,
            question=question,
            cards=json.dumps(cards),
            answer=answer
        )
        session.add(reading)
        await session.commit()