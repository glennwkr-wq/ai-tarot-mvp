from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from app.services.tarot.engine import draw_cards
from app.providers.llm.openai import generate_tarot_answer
from app.bot.handlers.start import get_main_keyboard
from app.services.user_service import (
    get_balance,
    change_balance,
    get_user,
    get_display_balance,
    can_use_free_card_today,
    mark_card_of_day_used,
)
from app.services.reading_service import save_reading

router = Router()


# ===================== FSM =====================

class TarotStates(StatesGroup):
    waiting_for_question = State()


# ===================== KEYBOARDS =====================

def get_skip_keyboard():
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="⏭ Пропустить")],
            [types.KeyboardButton(text="🔙 Меню")]
        ],
        resize_keyboard=True
    )


def get_after_reading_keyboard():
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="🔮 Новый расклад")],
            [types.KeyboardButton(text="🔙 Меню")],
        ],
        resize_keyboard=True
    )


# ===================== 🔮 СТАРТ РАСКЛАДА =====================

@router.message(F.text.in_(["🔮 Расклад", "🔮 Новый расклад"]))
async def start_spread(message: types.Message, state: FSMContext):
    await state.set_state(TarotStates.waiting_for_question)

    await message.answer(
        "✨ Если у вас есть вопрос — напишите его.\n\n"
        "Или нажмите «Пропустить», чтобы сделать общий расклад.",
        reply_markup=get_skip_keyboard()
    )


# ===================== ⏭ ПРОПУСК =====================

@router.message(F.text == "⏭ Пропустить")
async def skip_question(message: types.Message, state: FSMContext):
    await state.clear()
    await process_reading(message, "Общий расклад", mode="general")


# ===================== 💬 ВОПРОС =====================

@router.message(
    TarotStates.waiting_for_question,
    F.text & ~F.text.in_(["⏭ Пропустить", "🔙 Меню"])
)
async def handle_question(message: types.Message, state: FSMContext):
    await state.clear()
    await process_reading(message, message.text, mode="general")


# ===================== ❤️ ОТНОШЕНИЯ =====================

@router.message(F.text == "❤️ На отношения")
async def love_reading(message: types.Message):
    await process_reading(message, "Расклад на отношения", mode="love")


# ===================== 🃏 КАРТА ДНЯ =====================

@router.message(F.text == "🃏 Карта дня")
async def card_of_day(message: types.Message):
    user = await get_user(message.from_user.id)

    if not user:
        await message.answer("⚠️ Пользователь не найден. Нажмите /start")
        return

    is_free_today = await can_use_free_card_today(user)

    if not is_free_today:
        balance = await get_balance(message.from_user.id)
        if balance < 10:
            await message.answer("❌ Недостаточно кредитов.")
            return
        await change_balance(message.from_user.id, -10)

    cards = draw_cards(1)
    card = cards[0]

    await message.answer_photo(
        photo=card["image_id"],
        caption=f"🃏 <b>{card['name']}</b>",
        parse_mode="HTML"
    )

    try:
        reading = await generate_tarot_answer("Карта дня", cards, mode="daily")
    except Exception as e:
        print(f"Card of day error: {e}")
        reading = (
            f"🃏 <b>Карта дня — {card['name']}</b>\n\n"
            f"✨ {card['general']}\n\n"
            f"💡 Совет: {card['advice']}"
        )

    await mark_card_of_day_used(message.from_user.id)

    await message.answer(
        reading,
        parse_mode="HTML",
        reply_markup=get_main_keyboard()
    )


# ===================== 💰 БАЛАНС =====================

@router.message(F.text == "💰 Баланс")
async def balance_handler(message: types.Message):
    balance = await get_balance(message.from_user.id)

    await message.answer(
        f"💰 Ваш баланс: {balance}",
        reply_markup=get_main_keyboard()
    )


# ===================== 👤 ПРОФИЛЬ =====================

@router.message(F.text == "👤 Профиль")
async def profile_handler(message: types.Message):
    user = await get_user(message.from_user.id)
    balance = await get_display_balance(user)

    await message.answer(
        f"👤 Профиль\n\n"
        f"Имя: {user.name}\n"
        f"Дата рождения: {user.birthdate}\n"
        f"Знак: {user.zodiac}\n"
        f"Баланс: {balance}",
        reply_markup=get_main_keyboard()
    )


# ===================== 📜 ИСТОРИЯ УБРАНА =====================

@router.message(F.text == "📜 История")
async def history_removed(message: types.Message):
    await message.answer(
        "📜 Раздел истории убран из бота.\n\n"
        "Сейчас мы сосредоточены на качестве самих раскладов.",
        reply_markup=get_main_keyboard()
    )


# ===================== 🔙 МЕНЮ =====================

@router.message(F.text == "🔙 Меню")
async def back_to_menu(message: types.Message, state: FSMContext):
    await state.clear()

    await message.answer(
        "Главное меню:",
        reply_markup=get_main_keyboard()
    )


# ===================== 🧠 ОБЩАЯ ЛОГИКА =====================

async def process_reading(message: types.Message, question: str, mode: str = "general"):
    user_id = message.from_user.id

    balance = await get_balance(user_id)

    if balance < 10:
        await message.answer("❌ Недостаточно кредитов.")
        return

    await message.answer("🔮 Смотрю карты...")

    try:
        cards = draw_cards(3)

        cards_text = "\n".join([f"• {c['name']}" for c in cards])
        await message.answer(f"🃏 Выпали карты:\n{cards_text}")

        media = []

        for i, card in enumerate(cards):
            media.append(
                types.InputMediaPhoto(
                    media=card["image_id"],
                )
            )

        await message.answer_media_group(media)

        reading = await generate_tarot_answer(question, cards, mode=mode)

        await change_balance(user_id, -10)

    except Exception as e:
        print(f"Tarot error: {e}")
        await message.answer("⚠️ Произошла ошибка. Попробуйте позже.")
        return

    await save_reading(user_id, question, cards, reading)

    await message.answer(reading, reply_markup=get_after_reading_keyboard())