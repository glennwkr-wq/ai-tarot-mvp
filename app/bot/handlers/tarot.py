from aiogram import Router, types
import random

from app.services.tarot.engine import draw_cards
from app.providers.llm.openai import generate_tarot_answer

router = Router()

cards = [
    "Шут", "Маг", "Жрица", "Императрица", "Император",
    "Иерофант", "Влюбленные", "Колесница", "Сила", "Отшельник",
    "Колесо фортуны", "Справедливость", "Повешенный", "Смерть",
    "Умеренность", "Дьявол", "Башня", "Звезда", "Луна", "Солнце",
    "Суд", "Мир"
]


@router.message()
async def tarot_handler(message: types.Message):
    question = message.text

    cards = draw_cards(3)

    await message.answer("🔮 Думаю над раскладом...")

    try:
        reading = await generate_tarot_answer(question, cards)

        card_names = [c["name"] for c in cards]

        await message.answer(
            f"🃏 Ваши карты: {', '.join(card_names)}\n\n{reading}"
        )

    except Exception as e:
        await message.answer("⚠️ Ошибка при обращении к AI.")
        print("AI ERROR:", e)