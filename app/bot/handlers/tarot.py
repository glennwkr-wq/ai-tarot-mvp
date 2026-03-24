from aiogram import Router, types, F

from app.services.tarot.engine import draw_cards
from app.providers.llm.openai import generate_tarot_answer
from app.bot.handlers.start import get_main_keyboard
from app.services.user_service import get_balance, change_balance, get_user

router = Router()


waiting_for_question = set()


def get_after_reading_keyboard():
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [
                types.KeyboardButton(text="💬 Уточнить вопрос"),
                types.KeyboardButton(text="🃏 Доп карта"),
            ],
            [
                types.KeyboardButton(text="🔄 Новый расклад"),
                types.KeyboardButton(text="🔙 Меню"),
            ],
        ],
        resize_keyboard=True
    )


# ===================== 💰 БАЛАНС =====================

@router.message(F.text == "💰 Баланс")
async def balance_handler(message: types.Message):
    balance = await get_balance(message.from_user.id)

    await message.answer(
        f"💰 <b>Ваш баланс: {balance} кредитов</b>\n\n"
        "✨ 1 расклад = 1 кредит",
        parse_mode="HTML"
    )


# ===================== 👤 ПРОФИЛЬ =====================

@router.message(F.text == "👤 Профиль")
async def profile_handler(message: types.Message):
    user = await get_user(message.from_user.id)

    if not user:
        await message.answer("Ошибка профиля")
        return

    await message.answer(
        f"👤 <b>Ваш профиль</b>\n\n"
        f"Имя: {user.name}\n"
        f"Дата рождения: {user.birthdate}\n"
        f"Знак: {user.zodiac}\n"
        f"Баланс: {user.balance}",
        parse_mode="HTML"
    )


# ===================== 💬 ЗАДАТЬ ВОПРОС =====================

@router.message(F.text == "💬 Задать вопрос")
async def ask_question_start(message: types.Message):
    waiting_for_question.add(message.from_user.id)

    await message.answer(
        "✨ Задайте ваш вопрос...\n\n"
        "Карты подскажут направление 🌙"
    )


# ===================== 🃏 КАРТА ДНЯ =====================

@router.message(F.text == "🃏 Карта дня")
async def card_of_the_day(message: types.Message):
    card = draw_cards(1)[0]

    await message.answer(
        f"🃏 <b>Карта дня — {card['name']}</b>\n\n"
        f"{card['meaning']}",
        parse_mode="HTML"
    )


# ===================== 🔮 РАСКЛАД =====================

@router.message(F.text == "🔮 Расклад")
async def tarot_no_question(message: types.Message):
    user_id = message.from_user.id

    if await get_balance(user_id) <= 0:
        await message.answer("❌ Недостаточно кредитов.")
        return

    await change_balance(user_id, -1)

    cards = draw_cards(3)

    await message.answer("🔮 Делаю расклад...")

    reading = await generate_tarot_answer(
        question="Общий расклад",
        cards=cards
    )

    await message.answer(reading)


# ===================== 💬 ОБРАБОТКА ВОПРОСА =====================

@router.message()
async def handle_text(message: types.Message):
    user_id = message.from_user.id

    if user_id in waiting_for_question:
        waiting_for_question.remove(user_id)

        if await get_balance(user_id) <= 0:
            await message.answer("❌ Недостаточно кредитов.")
            return

        await change_balance(user_id, -1)

        cards = draw_cards(3)

        await message.answer("🔮 Смотрю карты...")

        reading = await generate_tarot_answer(message.text, cards)

        await message.answer(reading)

        return