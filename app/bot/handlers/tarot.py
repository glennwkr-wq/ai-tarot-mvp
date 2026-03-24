from aiogram import Router, types, F

from app.services.tarot.engine import draw_cards
from app.providers.llm.openai import generate_tarot_answer
from app.bot.handlers.start import get_main_keyboard
from app.services.user_service import get_balance, change_balance, get_user, get_display_balance
from app.services.reading_service import save_reading

router = Router()

waiting_for_question = set()


def get_after_reading_keyboard():
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="💬 Уточнить вопрос")],
            [types.KeyboardButton(text="🔙 Меню")],
        ],
        resize_keyboard=True
    )


# ===================== 💰 БАЛАНС =====================

@router.message(F.text == "💰 Баланс")
async def balance_handler(message: types.Message):
    balance = await get_balance(message.from_user.id)

    await message.answer(
        f"💰 <b>Ваш баланс: {balance} кредитов</b>",
        parse_mode="HTML"
    )


# ===================== 👤 ПРОФИЛЬ =====================

@router.message(F.text == "👤 Профиль")
async def profile_handler(message: types.Message):
    user = await get_user(message.from_user.id)

    balance = await get_display_balance(user)

    await message.answer(
        f"👤 <b>Ваш профиль</b>\n\n"
        f"Имя: {user.name}\n"
        f"Дата рождения: {user.birthdate}\n"
        f"Знак: {user.zodiac}\n"
        f"Баланс: {balance}",
        parse_mode="HTML"
    )


# ===================== 💬 ВОПРОС =====================

@router.message(F.text == "💬 Задать вопрос")
async def ask_question_start(message: types.Message):
    waiting_for_question.add(message.from_user.id)

    await message.answer("✨ Напишите ваш вопрос...")


# ===================== 🔮 РАСКЛАД =====================

async def safe_generate(question, cards):
    try:
        return await generate_tarot_answer(question, cards)
    except:
        # fallback
        return (
            "Карты указывают на важный период.\n\n"
            "Сейчас многое зависит от ваших решений.\n"
            "Доверьтесь внутреннему ощущению."
        )


@router.message(F.text == "🔮 Расклад")
async def tarot_no_question(message: types.Message):
    user_id = message.from_user.id

    if await get_balance(user_id) <= 0:
        await message.answer("❌ Недостаточно кредитов.")
        return

    await change_balance(user_id, -1)

    cards = draw_cards(3)

    await message.answer("🔮 Делаю расклад...")

    reading = await safe_generate("Общий расклад", cards)

    await save_reading(user_id, "Общий расклад", cards, reading)

    await message.answer(reading)


# ===================== 💬 ОБРАБОТКА =====================

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

        reading = await safe_generate(message.text, cards)

        await save_reading(user_id, message.text, cards, reading)

        await message.answer(reading)

        return