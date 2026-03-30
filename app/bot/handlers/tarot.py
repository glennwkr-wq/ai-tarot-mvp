from aiogram import Router, types, F
import asyncio
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from app.bot.handlers.start import zodiac_with_emoji

from sqlalchemy import select
from app.db.session import SessionLocal
from app.models.user import User

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
from app.core.config import settings

router = Router()

# ===================== PROCESS LOCK =====================

async def is_user_processing(state: FSMContext) -> bool:
    data = await state.get_data()
    return data.get("is_processing", False)


async def set_processing(state: FSMContext, value: bool):
    data = await state.get_data()
    data["is_processing"] = value
    await state.set_data(data)

# ===================== FSM =====================

class TarotStates(StatesGroup):
    waiting_for_question = State()


# 👇 ДОБАВЛЕНО: FSM ПОДДЕРЖКИ
class SupportStates(StatesGroup):
    waiting_for_message = State()


# 👇 ДОБАВЛЕНО: FSM ДА/НЕТ
class YesNoStates(StatesGroup):
    waiting_for_question = State()


# 👇 ДОБАВЛЕНО: FSM FOLLOWUP
class FollowupStates(StatesGroup):
    waiting_for_input = State()

class AdminCreditStates(StatesGroup):
    waiting_for_user_id = State()
    waiting_for_amount = State()

class AdminBroadcastStates(StatesGroup):
    waiting_for_target = State()
    waiting_for_text = State()
    waiting_for_confirm = State()

# ===================== MODERATION =====================

def is_question_allowed(text: str) -> bool:
    text = text.lower()

    banned_keywords = [
        "умру", "смерть", "когда я умру",
        "убить", "убийство",
        "болезнь", "диагноз", "рак",
        "суицид",
        "секс", "порно",
        "наркот",
        "оскорб", "тварь", "ненавижу"
    ]

    return not any(word in text for word in banned_keywords)


def get_refusal_message() -> str:
    return (
        "🔮 Карты не работают с такими вопросами.\n\n"
        "Но мы можем посмотреть, что сейчас важно для вас "
        "и куда лучше направить свою энергию."
    )


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
            [types.KeyboardButton(text="🔮 Новый расклад 10💰")],
            [types.KeyboardButton(text="🔙 Меню")],
        ],
        resize_keyboard=True
    )


# 👇 ДОБАВЛЕНО: FOLLOWUP KEYBOARD
def get_followup_keyboard():
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="➕ Доп карта 10💰")],
            [types.KeyboardButton(text="✍️ Уточнить 10💰")],
            [types.KeyboardButton(text="🔙 Меню")],
        ],
        resize_keyboard=True
    )


# ===================== ❓ ДА / НЕТ =====================

@router.message(F.text == "❓ Да / Нет 10💰")
async def yesno_start(message: types.Message, state: FSMContext):

    if await is_user_processing(state):
        await message.answer("🔮 Карты уже раскрываются… Пожалуйста, подождите.")
        return

    await state.set_state(YesNoStates.waiting_for_question)

    await message.answer(
        "Задайте вопрос, на который можно ответить «да» или «нет».",
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=[[types.KeyboardButton(text="🔙 Меню")]],
            resize_keyboard=True
        )
    )


@router.message(YesNoStates.waiting_for_question, F.text & ~F.text.in_(["🔙 Меню"]))
async def yesno_process(message: types.Message, state: FSMContext):
    await state.clear()

    if await is_user_processing(state):
        await message.answer("🔮 Карты уже раскрываются… Пожалуйста, подождите.")
        return

    if not is_question_allowed(message.text):
        await message.answer(
            get_refusal_message(),
            reply_markup=get_main_keyboard(message.from_user.id)
        )
        return

    user_id = message.from_user.id

    balance = await get_balance(user_id)
    if balance < 10:
        await message.answer("❌ Недостаточно кредитов.")
        return
    await set_processing(state, True)
    await message.answer("🔮 Смотрю карты...")

    try:
        cards = draw_cards(1)
        card = cards[0]

        await message.answer_photo(
            photo=card["image_id"],
            caption=f"🃏 <b>{card['name']}</b>",
            parse_mode="HTML"
        )

        reading = await generate_tarot_answer(message.text, cards, mode="yesno")

        await change_balance(user_id, -10)

    except Exception as e:
        print(f"Yes/No error: {e}")
        await message.answer("⚠️ Произошла ошибка. Попробуйте позже.")
        await set_processing(state, False)
        return

    await save_reading(user_id, message.text, cards, reading)

    await message.answer(reading, reply_markup=get_main_keyboard(message.from_user.id))
    await set_processing(state, False)

# ===================== 🛟 ПОДДЕРЖКА =====================

@router.message(F.text == "🛟 Поддержка")
async def support_start(message: types.Message, state: FSMContext):
    await state.set_state(SupportStates.waiting_for_message)

    await message.answer(
        "📩 Напишите Ваш вопрос — я передам его в поддержку.\n\n"
        "Мы ответим Вам здесь.",
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=[[types.KeyboardButton(text="🔙 Меню")]],
            resize_keyboard=True
        )
    )

@router.message(F.text == "➕ Начислить кредиты")
async def admin_give_credits_start(message: types.Message, state: FSMContext):
    if message.from_user.id != settings.SUPPORT_ADMIN_ID:
        return

    await state.set_state(AdminCreditStates.waiting_for_user_id)

    await message.answer(
        "Введите Telegram ID пользователя, которому нужно начислить кредиты:",
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=[[types.KeyboardButton(text="🔙 Меню")]],
            resize_keyboard=True
        )
    )

@router.message(F.text == "📢 Сообщение пользователям")
async def admin_broadcast_start(message: types.Message, state: FSMContext):
    if message.from_user.id != settings.SUPPORT_ADMIN_ID:
        return

    await state.set_state(AdminBroadcastStates.waiting_for_target)

    await message.answer(
        "Введите Telegram ID пользователя\nили нажмите кнопку «Отправить всем»:",
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=[
                [types.KeyboardButton(text="📨 Отправить всем")],
                [types.KeyboardButton(text="🔙 Меню")]
            ],
            resize_keyboard=True
        )
    )

@router.message(AdminBroadcastStates.waiting_for_target, F.text & ~F.text.in_(["🔙 Меню"]))
async def admin_broadcast_choose_target(message: types.Message, state: FSMContext):
    if message.from_user.id != settings.SUPPORT_ADMIN_ID:
        await state.clear()
        return

    text = message.text.strip()

    if text == "📨 Отправить всем":
        await state.update_data(target="all")

    elif text.isdigit():
        target_id = int(text)
        user = await get_user(target_id)

        if not user:
            await state.clear()
            await message.answer(
                "❌ Пользователь не найден.",
                reply_markup=get_main_keyboard(message.from_user.id)
            )
            return

        await state.update_data(target=target_id)

    else:
        await message.answer("⚠️ Введите корректный ID или выберите кнопку.")
        return

    await state.set_state(AdminBroadcastStates.waiting_for_text)

    await message.answer(
        "Введите текст сообщения:",
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=[[types.KeyboardButton(text="🔙 Меню")]],
            resize_keyboard=True
        )
    )

@router.message(AdminBroadcastStates.waiting_for_text, F.text & ~F.text.in_(["🔙 Меню"]))
async def admin_broadcast_text(message: types.Message, state: FSMContext):
    if message.from_user.id != settings.SUPPORT_ADMIN_ID:
        await state.clear()
        return

    await state.update_data(text=message.text)

    data = await state.get_data()

    target = data["target"]

    target_text = "ВСЕМ пользователям" if target == "all" else f"пользователю {target}"

    await state.set_state(AdminBroadcastStates.waiting_for_confirm)

    await message.answer(
        f"Вы собираетесь отправить сообщение:\n\n"
        f"{message.text}\n\n"
        f"Получатель: {target_text}\n\n"
        f"Подтвердить отправку?",
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=[
                [types.KeyboardButton(text="✅ Отправить")],
                [types.KeyboardButton(text="🔙 Меню")]
            ],
            resize_keyboard=True
        )
    )

@router.message(AdminBroadcastStates.waiting_for_confirm, F.text == "✅ Отправить")
async def admin_broadcast_send(message: types.Message, state: FSMContext):
    if message.from_user.id != settings.SUPPORT_ADMIN_ID:
        await state.clear()
        return

    data = await state.get_data()
    target = data["target"]
    text = data["text"]

    success = 0
    failed = 0

    if target == "all":
        async with SessionLocal() as session:
            result = await session.execute(select(User))
            users = result.scalars().all()

        for user in users:
            try:
                await message.bot.send_message(user.telegram_id, text)
                success += 1
            except Exception:
                failed += 1

    else:
        try:
            await message.bot.send_message(target, text)
            success += 1
        except Exception:
            failed += 1

    await state.clear()

    await message.answer(
        f"✅ Рассылка завершена\n\n"
        f"Успешно: {success}\n"
        f"Ошибки: {failed}",
        reply_markup=get_main_keyboard(message.from_user.id)
    )

@router.message(
    AdminBroadcastStates.waiting_for_target,
    F.text == "🔙 Меню"
)
@router.message(
    AdminBroadcastStates.waiting_for_text,
    F.text == "🔙 Меню"
)
@router.message(
    AdminBroadcastStates.waiting_for_confirm,
    F.text == "🔙 Меню"
)
async def admin_broadcast_cancel(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Главное меню:",
        reply_markup=get_main_keyboard(message.from_user.id)
    )

@router.message(AdminCreditStates.waiting_for_user_id, F.text & ~F.text.in_(["🔙 Меню"]))
async def admin_give_credits_get_user_id(message: types.Message, state: FSMContext):
    if message.from_user.id != settings.SUPPORT_ADMIN_ID:
        await state.clear()
        return

    text = message.text.strip()

    if not text.isdigit():
        await message.answer("⚠️ ID должен быть числом. Попробуйте ещё раз.")
        return

    target_telegram_id = int(text)
    user = await get_user(target_telegram_id)

    if not user:
        await state.clear()
        await message.answer(
            "❌ Пользователь с таким Telegram ID не найден.",
            reply_markup=get_main_keyboard(message.from_user.id)
        )
        return

    await state.update_data(target_telegram_id=target_telegram_id)

    await state.set_state(AdminCreditStates.waiting_for_amount)

    await message.answer(
        f"Пользователь найден: {user.name}\n\n"
        f"Введите количество кредитов для начисления:",
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=[[types.KeyboardButton(text="🔙 Меню")]],
            resize_keyboard=True
        )
    )

@router.message(AdminCreditStates.waiting_for_amount, F.text & ~F.text.in_(["🔙 Меню"]))
async def admin_give_credits_finish(message: types.Message, state: FSMContext):
    if message.from_user.id != settings.SUPPORT_ADMIN_ID:
        await state.clear()
        return

    text = message.text.strip()

    if not text.isdigit():
        await message.answer("⚠️ Сумма должна быть положительным числом. Попробуйте ещё раз.")
        return

    amount = int(text)

    if amount <= 0:
        await message.answer("⚠️ Сумма должна быть больше нуля.")
        return

    data = await state.get_data()
    target_telegram_id = data.get("target_telegram_id")

    if not target_telegram_id:
        await state.clear()
        await message.answer(
            "⚠️ Не удалось получить ID пользователя. Попробуйте заново.",
            reply_markup=get_main_keyboard(message.from_user.id)
        )
        return

    user = await get_user(target_telegram_id)
    if not user:
        await state.clear()
        await message.answer(
            "❌ Пользователь больше не найден.",
            reply_markup=get_main_keyboard(message.from_user.id)
        )
        return

    await change_balance(target_telegram_id, amount)

    await state.clear()

    await message.answer(
        f"✅ Начислено {amount} кредитов пользователю {user.name} ({target_telegram_id}).",
        reply_markup=get_main_keyboard(message.from_user.id)
    )

    try:
        await message.bot.send_message(
            target_telegram_id,
            f"🎁 Вам подарок от разработчика!\n\n"
            f"✨ На ваш баланс начислено {amount} кредитов."
        )
    except Exception:
        await message.answer(
            "⚠️ Кредиты начислены, но уведомление пользователю отправить не удалось."
        )

@router.message(SupportStates.waiting_for_message, F.text & ~F.text.in_(["🔙 Меню"]))
async def support_send(message: types.Message, state: FSMContext):
    user = await get_user(message.from_user.id)

    text = (
        f"📩 Сообщение в поддержку\n\n"
        f"👤 {user.name}\n"
        f"ID: {message.from_user.id}\n\n"
        f"{message.text}"
    )

    await message.bot.send_message(settings.SUPPORT_ADMIN_ID, text)

    await state.clear()

    await message.answer(
        "✨ Ваше сообщение отправлено.\n"
        "Мы скоро ответим Вам.",
        reply_markup=get_main_keyboard(message.from_user.id)
    )


# 👇 ответ админа
@router.message(F.reply_to_message)
async def admin_reply(message: types.Message):
    if message.from_user.id not in settings.admin_ids:
        return

    original_text = message.reply_to_message.text

    if not original_text or "ID:" not in original_text:
        return

    try:
        user_id = int(original_text.split("ID:")[1].split("\n")[0].strip())
    except:
        return

    await message.bot.send_message(
        user_id,
        f"💬 Ответ поддержки:\n\n{message.text}",
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=[
                [types.KeyboardButton(text="🛟 Поддержка")],
                [types.KeyboardButton(text="🔙 Меню")]
            ],
            resize_keyboard=True
        )
    )


# ===================== 🔮 СТАРТ РАСКЛАДА =====================

@router.message(F.text.in_(["🔮 Расклад 10💰", "🔮 Новый расклад 10💰"]))
async def start_spread(message: types.Message, state: FSMContext):
    
    if await is_user_processing(state):
        await message.answer("🔮 Карты уже раскрываются… Пожалуйста, подождите.")
        return
    
    await state.set_state(TarotStates.waiting_for_question)

    await message.answer(
        "✨ Если у Вас есть вопрос — напишите его.\n\n"
        "Или нажмите «Пропустить», чтобы сделать общий расклад.",
        reply_markup=get_skip_keyboard()
    )


# ===================== ⏭ ПРОПУСК =====================

@router.message(F.text == "⏭ Пропустить")
async def skip_question(message: types.Message, state: FSMContext):
    
    if await is_user_processing(state):
        await message.answer("🔮 Карты уже раскрываются… Пожалуйста, подождите.")
        return
    
    await state.clear()
    await process_reading(message, state, "Общий расклад", mode="general")


# ===================== 💬 ВОПРОС =====================

@router.message(
    TarotStates.waiting_for_question,
    F.text & ~F.text.in_(["⏭ Пропустить", "🔙 Меню"])
)
async def handle_question(message: types.Message, state: FSMContext):
    await state.clear()

    if await is_user_processing(state):
        await message.answer("🔮 Карты уже раскрываются… Пожалуйста, подождите.")
        return

    if not is_question_allowed(message.text):
        await message.answer(
            get_refusal_message(),
            reply_markup=get_main_keyboard(message.from_user.id)
        )
        return

    await process_reading(message, state, message.text, mode="general")


# ===================== ❤️ ОТНОШЕНИЯ =====================

@router.message(F.text == "❤️ На отношения 10💰")
async def love_reading(message: types.Message, state: FSMContext):
    
    if await is_user_processing(state):
        await message.answer("🔮 Карты уже раскрываются… Пожалуйста, подождите.")
        return
    
    await process_reading(message, state, "Расклад на отношения", mode="love")


# ===================== 💼 КАРЬЕРА =====================

@router.message(F.text == "💼 На карьеру 10💰")
async def career_reading(message: types.Message, state: FSMContext):
    
    if await is_user_processing(state):
        await message.answer("🔮 Карты уже раскрываются… Пожалуйста, подождите.")
        return

    await process_reading(message, state, "Расклад на карьеру", mode="career")

@router.message(F.text == "🗓 Расклад на год 50💰")
async def year_reading(message: types.Message, state: FSMContext):

    if await is_user_processing(state):
        await message.answer("🔮 Карты уже раскрываются… Пожалуйста, подождите.")
        return

    await process_reading(
        message,
        state,
        "Расклад на год",
        mode="year",
        card_count=12,
        price=50,
        enable_followup=False
    )

# ===================== ➕ ДОП КАРТА =====================

@router.message(F.text == "➕ Доп карта 10💰")
async def extra_card(message: types.Message, state: FSMContext):

    if await is_user_processing(state):
        await message.answer("🔮 Карты уже раскрываются… Пожалуйста, подождите.")
        return

    data = await state.get_data()
    if not data:
        return

    user_id = message.from_user.id

    balance = await get_balance(user_id)
    if balance < 10:
        await message.answer("❌ Недостаточно кредитов.")
        return
    await set_processing(state, True)
    await message.answer("🔮 Тяну дополнительную карту...")
    try:
        card = draw_cards(1)[0]

        await message.answer_photo(
            photo=card["image_id"],
            caption=f"🃏 <b>{card['name']}</b>",
            parse_mode="HTML"
        )
        new_cards = data["cards"] + [card]

        reading = await generate_tarot_answer(
            data["question"],
            new_cards,
            mode="followup",
            previous_answer=data.get("last_answer"),
            followup_type="extra_card"
        )

        await change_balance(user_id, -10)

        await state.update_data(cards=new_cards, last_answer=reading)

        await message.answer(reading, reply_markup=get_followup_keyboard())
    except Exception as e:
        print(f"Extra card error: {e}")
        await message.answer("⚠️ Произошла ошибка. Попробуйте позже.")

    finally:
        await set_processing(state, False)

# ===================== ✍️ УТОЧНЕНИЕ =====================

@router.message(F.text == "✍️ Уточнить 10💰")
async def уточнение_start(message: types.Message, state: FSMContext):

    if await is_user_processing(state):
        await message.answer("🔮 Карты уже раскрываются… Пожалуйста, подождите.")
        return

    await state.set_state(FollowupStates.waiting_for_input)

    await message.answer(
        "Напишите, что хотите уточнить:",
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=[[types.KeyboardButton(text="🔙 Меню")]],
            resize_keyboard=True
        )
    )


@router.message(FollowupStates.waiting_for_input, F.text & ~F.text.in_(["🔙 Меню"]))
async def уточнение_process(message: types.Message, state: FSMContext):

    if await is_user_processing(state):
        await message.answer("🔮 Карты уже раскрываются… Пожалуйста, подождите.")
        return

    data = await state.get_data()

    user_id = message.from_user.id

    balance = await get_balance(user_id)
    if balance < 10:
        await message.answer("❌ Недостаточно кредитов.")
        return
    await set_processing(state, True)
    await message.answer("🔮 Уточняю расклад...")
    try:
        clarification_question = (
            f"Исходный вопрос: {data['question']}\n"
            f"Уточнение пользователя: {message.text}"
        )

        reading = await generate_tarot_answer(
            clarification_question,
            data["cards"],
            mode="followup",
            previous_answer=data.get("last_answer"),
            followup_type="clarification"
        )

        await change_balance(user_id, -10)

        await state.clear()
        await state.update_data(
            question=data["question"],
            cards=data["cards"],
            mode=data["mode"],
            last_answer=reading
        )

        await message.answer(reading, reply_markup=get_followup_keyboard())
    except Exception as e:
        print(f"Clarification error: {e}")
        await message.answer("⚠️ Произошла ошибка. Попробуйте позже.")

    finally:
        await set_processing(state, False)

# ===================== 🃏 КАРТА ДНЯ =====================

@router.message(F.text == "🃏 Карта дня 10💰")
async def card_of_day(message: types.Message, state: FSMContext):

    if await is_user_processing(state):
        await message.answer("🔮 Карты уже раскрываются… Пожалуйста, подождите.")
        return

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
    await set_processing(state, True)
    await message.answer_photo(
        photo=card["image_id"],
        caption=f"🃏 <b>{card['name']}</b>",
        parse_mode="HTML"
    )

    await asyncio.sleep(1)
    await message.answer("🔮 Читаю карту дня...")

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
        reply_markup=get_main_keyboard(message.from_user.id)
    )
    await set_processing(state, False)

# ===================== 💰 БАЛАНС =====================

@router.message(F.text == "💰 Баланс")
async def balance_handler(message: types.Message):
    balance = await get_balance(message.from_user.id)

    await message.answer(
        f"💰 Ваш баланс: {balance}",
        reply_markup=get_main_keyboard(message.from_user.id)
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
        f"Знак: {zodiac_with_emoji(user.zodiac)}\n"
        f"Баланс: {balance}",
        reply_markup=get_main_keyboard(message.from_user.id)
    )


# ===================== 📜 ИСТОРИЯ УБРАНА =====================

@router.message(F.text == "📜 История")
async def history_removed(message: types.Message):
    await message.answer(
        "📜 Раздел истории убран из бота.\n\n"
        "Сейчас мы сосредоточены на качестве самих раскладов.",
        reply_markup=get_main_keyboard(message.from_user.id)
    )


# ===================== 🔙 МЕНЮ =====================

@router.message(F.text == "🔙 Меню")
async def back_to_menu(message: types.Message, state: FSMContext):
    await state.clear()

    await message.answer(
        "Главное меню:",
        reply_markup=get_main_keyboard(message.from_user.id)
    )


# ===================== 🧠 ОБЩАЯ ЛОГИКА =====================

async def process_reading(
    message: types.Message,
    state: FSMContext,
    question: str,
    mode: str = "general",
    card_count: int = 3,
    price: int = 10,
    enable_followup: bool = True
):
    user_id = message.from_user.id

    if await is_user_processing(state):
        await message.answer("🔮 Карты уже раскрываются… Пожалуйста, подождите.")
        return

    await set_processing(state, True)

    balance = await get_balance(user_id)

    if balance < price:
        await message.answer("❌ Недостаточно кредитов.")
        await set_processing(state, False)
        return

    try:
        cards = draw_cards(card_count)

        cards_text = "\n".join([f"• {c['name']}" for c in cards])
        await message.answer(f"🃏 Выпали карты:\n{cards_text}")

        await asyncio.sleep(1)

        media = []

        for i, card in enumerate(cards):
            media.append(
                types.InputMediaPhoto(
                    media=card["image_id"],
                )
            )

        if len(media) <= 6:
            await message.answer_media_group(media)
        else:
            await message.answer_media_group(media[:6])
            await message.answer_media_group(media[6:])

        await asyncio.sleep(1)

        if mode == "year":
            await message.answer("🔮 Читаю расклад на год...")
        else:
            await message.answer("🔮 Читаю карты...")        

        await asyncio.sleep(1)

        reading = await generate_tarot_answer(question, cards, mode=mode)

        await change_balance(user_id, -price)

    except Exception as e:
        print(f"Tarot error: {e}")
        await message.answer("⚠️ Произошла ошибка. Попробуйте позже.")
        await set_processing(state, False)
        return

    await save_reading(user_id, question, cards, reading)

    if enable_followup:
        await state.update_data(
            question=question,
            cards=cards,
            mode=mode,
            last_answer=reading
        )

        await message.answer(reading, reply_markup=get_followup_keyboard())
        await set_processing(state, False)
    else:
        await state.clear()
        await message.answer(
            reading,
            reply_markup=get_main_keyboard(message.from_user.id)
        )
        await set_processing(state, False)