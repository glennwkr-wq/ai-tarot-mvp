from aiogram import Router
from aiogram.types import Message

from app.services.tarot.engine import draw_cards

router = Router()


@router.message()
async def tarot_handler(message: Message):
    cards = draw_cards(3)

    text = "🔮 Ваш расклад:\n\n"

    for i, card in enumerate(cards, start=1):
        position = "🔻 перевёрнутая" if card["reversed"] else "🔺 прямая"

        text += f"{i}. {card['name']} ({position})\n"
        text += f"— {card['meaning']}\n\n"

    text += "✨ Прислушайтесь к себе — ответ уже внутри вас."

    await message.answer(text)