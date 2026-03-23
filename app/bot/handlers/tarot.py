from aiogram import Router, types, F

from app.services.tarot.engine import draw_cards
from app.providers.llm.openai import generate_tarot_answer

router = Router()


# 🔮 Расклад
@router.message(F.text == "🔮 Сделать расклад")
async def start_tarot(message: types.Message):
    await message.answer("Задайте ваш вопрос 🔮")


@router.message()
async def tarot_handler(message: types.Message):
    # ❗ игнорируем кнопки меню
    if message.text in ["🔮 Сделать расклад", "🃏 Карта дня", "💰 Баланс"]:
        return

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