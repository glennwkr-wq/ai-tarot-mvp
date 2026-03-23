from aiogram import Router, types
import random

from app.services.tarot.engine import generate_tarot_reading

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

```
selected_cards = random.sample(cards, 3)

await message.answer("🔮 Думаю над раскладом...")

try:
    reading = generate_tarot_reading(selected_cards, question)

    await message.answer(
        f"🃏 Твои карты: {', '.join(selected_cards)}\n\n{reading}"
    )

except Exception as e:
    await message.answer("⚠️ Ошибка при обращении к AI. Попробуй позже.")
    print("AI ERROR:", e)