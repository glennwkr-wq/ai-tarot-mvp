from aiogram import Router, types, F

router = Router()


def get_buy_coins_keyboard():
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [
                types.KeyboardButton(text="50 монет — 99₽"),
                types.KeyboardButton(text="100 монет — 149₽"),
            ],
            [
                types.KeyboardButton(text="200 монет — 249₽"),
                types.KeyboardButton(text="500 монет — 449₽"),
            ],
            [
                types.KeyboardButton(text="200 монет — 249⭐"),
                types.KeyboardButton(text="500 монет — 449⭐"),
            ],
            [types.KeyboardButton(text="🔙 Меню")],
        ],
        resize_keyboard=True
    )


@router.message(F.text == "💳 Купить монеты")
async def open_buy_coins_menu(message: types.Message):
    await message.answer(
        "💰 Выберите пакет монет:\n\n",
        reply_markup=get_buy_coins_keyboard()
    )


@router.message(F.text == "50 монет — 99₽")
async def buy_50_rub(message: types.Message):
    await message.answer(
        "Вы выбрали пакет:\n\n"
        "💰 50 монет — 99₽\n\n"
        "Платёж через кассу подключим следующим шагом.",
        reply_markup=get_buy_coins_keyboard()
    )


@router.message(F.text == "100 монет — 149₽")
async def buy_100_rub(message: types.Message):
    await message.answer(
        "Вы выбрали пакет:\n\n"
        "💰 100 монет — 149₽\n\n"
        "Платёж через кассу подключим следующим шагом.",
        reply_markup=get_buy_coins_keyboard()
    )


@router.message(F.text == "200 монет — 249₽")
async def buy_200_rub(message: types.Message):
    await message.answer(
        "Вы выбрали пакет:\n\n"
        "💰 200 монет — 249₽\n\n"
        "Платёж через кассу подключим следующим шагом.",
        reply_markup=get_buy_coins_keyboard()
    )


@router.message(F.text == "500 монет — 449₽")
async def buy_500_rub(message: types.Message):
    await message.answer(
        "Вы выбрали пакет:\n\n"
        "💰 500 монет — 449₽\n\n"
        "Платёж через кассу подключим следующим шагом.",
        reply_markup=get_buy_coins_keyboard()
    )


@router.message(F.text == "200 монет — 249⭐")
async def buy_200_stars(message: types.Message):
    await message.answer(
        "Вы выбрали пакет:\n\n"
        "💰 200 монет — 249⭐\n\n"
        "Оплату через Telegram Stars подключим следующим шагом.",
        reply_markup=get_buy_coins_keyboard()
    )


@router.message(F.text == "500 монет — 449⭐")
async def buy_500_stars(message: types.Message):
    await message.answer(
        "Вы выбрали пакет:\n\n"
        "💰 500 монет — 449⭐\n\n"
        "Оплату через Telegram Stars подключим следующим шагом.",
        reply_markup=get_buy_coins_keyboard()
    )