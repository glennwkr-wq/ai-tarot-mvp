from aiogram import Router, types
from aiogram.filters import CommandStart

router = Router()


@router.message(CommandStart())
async def start_handler(message: types.Message):
    await message.answer(
        "✨ Добро пожаловать в AI Таролога\n\n"
        "Я помогу вам взглянуть на ситуацию через карты.\n\n"
        "Выберите, что хотите сделать:",
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=[
                [types.KeyboardButton(text="🔮 Сделать расклад")],
                [types.KeyboardButton(text="🃏 Карта дня")],
                [types.KeyboardButton(text="💰 Баланс")],
            ],
            resize_keyboard=True
        )
    )