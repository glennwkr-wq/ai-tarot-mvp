from aiogram import Router, types
from aiogram.filters import CommandStart

router = Router()


def get_main_keyboard():
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [
                types.KeyboardButton(text="🔮 Расклад"),
                types.KeyboardButton(text="🃏 Карта дня"),
            ],
            [
                types.KeyboardButton(text="💬 Задать вопрос"),
                types.KeyboardButton(text="❤️ На отношения"),
            ],
            [
                types.KeyboardButton(text="📜 История"),
                types.KeyboardButton(text="⚙️ Настройки"),
            ],
            [
                types.KeyboardButton(text="💰 Баланс"),
            ],
        ],
        resize_keyboard=True
    )


@router.message(CommandStart())
async def start_handler(message: types.Message):
    await message.answer(
        "🔮 <b>AI Таролог</b>\n\n"
        "Я помогу тебе разобраться в ситуации через карты.\n\n"
        "✨ Можно задать вопрос\n"
        "✨ Можно просто сделать расклад\n\n"
        "👇 Выбери действие:",
        reply_markup=get_main_keyboard(),
        parse_mode="HTML"
    )