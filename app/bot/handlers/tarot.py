from aiogram import Router, types
import random

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

    selected_cards = random.sample(cards, 3)

    await message.answer("🔮 Думаю над раскладом...")

    try:
        # 🤖 вызываем OpenAI
        reading = await generate_tarot_answer(question, selected_cards)

        await message.answer(
            f"🃏 Ваши карты: {', '.join(selected_cards)}\n\n{reading}"
        )

    except Exception as e:
        await message.answer("⚠️ Ошибка при обращении к AI. Попробуйте позже.")
        print("AI ERROR:", e)