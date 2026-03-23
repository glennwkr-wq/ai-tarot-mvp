from aiogram import Router, types, F

from app.services.tarot.engine import draw_cards
from app.providers.llm.openai import generate_tarot_answer
from app.bot.handlers.start import get_main_keyboard
from app.core.config import settings

router = Router()

# 💾 ВРЕМЕННОЕ ХРАНИЛИЩЕ БАЛАНСА
user_balances = {}


def get_balance(user_id: int) -> int:
    if user_id == settings.ADMIN_ID:
        return 9999
    return user_balances.get(user_id, 3)


def change_balance(user_id: int, amount: int):
    user_balances[user_id] = get_balance(user_id) + amount


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
    balance = get_balance(message.from_user.id)

    keyboard = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="💳 Купить 10 — 99⭐")],
            [types.KeyboardButton(text="💳 Купить 30 — 249⭐")],
            [types.KeyboardButton(text="🔙 Меню")],
        ],
        resize_keyboard=True
    )

    await message.answer(
        f"💰 <b>Ваш баланс: {balance} кредитов</b>\n\n"
        "✨ 1 расклад = 1 кредит\n\n"
        "Выберите пакет:",
        parse_mode="HTML",
        reply_markup=keyboard
    )


# ===================== 💳 ПОКУПКА (заглушка) =====================

@router.message(F.text.startswith("💳 Купить"))
async def buy_handler(message: types.Message):
    user_id = message.from_user.id

    if "10" in message.text:
        change_balance(user_id, 10)
        text = "✅ +10 кредитов зачислено!"
    elif "30" in message.text:
        change_balance(user_id, 30)
        text = "🔥 +30 кредитов зачислено!"
    else:
        text = "Ошибка пакета"

    await message.answer(
        f"{text}\n\n💰 Новый баланс: {get_balance(user_id)}",
        reply_markup=get_main_keyboard()
    )


# ===================== 🃏 КАРТА ДНЯ =====================

@router.message(F.text == "🃏 Карта дня")
async def card_of_the_day(message: types.Message):
    card = draw_cards(1)[0]

    await message.answer(
        f"🃏 <b>Карта дня — {card['name']}</b>\n\n"
        f"{card['meaning']}\n\n"
        "💡 Обрати внимание на эту энергию сегодня.",
        parse_mode="HTML",
        reply_markup=get_after_reading_keyboard()
    )


# ===================== 🔮 РАСКЛАД =====================

@router.message(F.text == "🔮 Расклад")
async def tarot_no_question(message: types.Message):
    user_id = message.from_user.id

    if get_balance(user_id) <= 0:
        await message.answer("❌ Недостаточно кредитов. Зайди в баланс.")
        return

    change_balance(user_id, -1)

    cards = draw_cards(3)

    await message.answer("🔮 Делаю расклад...")

    try:
        reading = await generate_tarot_answer(
            question="Общий расклад на текущую ситуацию",
            cards=cards
        )

        card_names = [c["name"] for c in cards]

        await message.answer(
            f"🃏 Ваши карты: {', '.join(card_names)}\n\n{reading}"
        )

        await message.answer(
            "✨ Что дальше?",
            reply_markup=get_after_reading_keyboard()
        )

    except Exception as e:
        await message.answer("⚠️ Ошибка при обращении к AI.")
        print("AI ERROR:", e)


# ===================== 💬 УТОЧНЕНИЕ =====================

@router.message(F.text == "💬 Уточнить вопрос")
async def ask_question(message: types.Message):
    await message.answer("Напиши уточняющий вопрос 🔮")


# ===================== 🃏 ДОП КАРТА =====================

@router.message(F.text == "🃏 Доп карта")
async def extra_card(message: types.Message):
    user_id = message.from_user.id

    if get_balance(user_id) <= 0:
        await message.answer("❌ Недостаточно кредитов.")
        return

    change_balance(user_id, -1)

    card = draw_cards(1)[0]

    await message.answer(
        f"🃏 Дополнительная карта: {card['name']}\n\n"
        f"{card['meaning']}",
        reply_markup=get_after_reading_keyboard()
    )


# ===================== 🔄 НОВЫЙ РАСКЛАД =====================

@router.message(F.text == "🔄 Новый расклад")
async def new_spread(message: types.Message):
    await tarot_no_question(message)


# ===================== 🔙 МЕНЮ =====================

@router.message(F.text == "🔙 Меню")
async def back_to_menu(message: types.Message):
    await message.answer(
        "Главное меню:",
        reply_markup=get_main_keyboard()
    )


# ===================== 💬 ВОПРОС =====================

@router.message()
async def tarot_with_question(message: types.Message):
    if message.text in [
        "🔮 Расклад",
        "🃏 Карта дня",
        "💰 Баланс",
        "💬 Уточнить вопрос",
        "🃏 Доп карта",
        "🔄 Новый расклад",
        "🔙 Меню",
        "💳 Купить 10 — 99⭐",
        "💳 Купить 30 — 249⭐",
    ]:
        return

    user_id = message.from_user.id

    if get_balance(user_id) <= 0:
        await message.answer("❌ Недостаточно кредитов.")
        return

    change_balance(user_id, -1)

    question = message.text
    cards = draw_cards(3)

    await message.answer("🔮 Думаю над раскладом...")

    try:
        reading = await generate_tarot_answer(question, cards)

        card_names = [c["name"] for c in cards]

        await message.answer(
            f"🃏 Ваши карты: {', '.join(card_names)}\n\n{reading}"
        )

        await message.answer(
            "✨ Что дальше?",
            reply_markup=get_after_reading_keyboard()
        )

    except Exception as e:
        await message.answer("⚠️ Ошибка при обращении к AI.")
        print("AI ERROR:", e)