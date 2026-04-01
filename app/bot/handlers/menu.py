from aiogram import Router, types, F

router = Router()


@router.message(F.text == "💰 Баланс")
async def balance_handler(message: types.Message):
    await message.answer("💰 Ваш баланс: 0 монет")


@router.message(F.text == "🃏 Карта дня")
async def card_of_day(message: types.Message):
    await message.answer("🃏 Ваша карта дня: Скоро добавим 🔮")