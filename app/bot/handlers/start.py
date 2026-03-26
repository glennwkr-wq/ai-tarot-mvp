from aiogram import Router, types, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from app.services.user_service import (
    get_user,
    create_user,
    update_user_name,
    update_user_birthdate,
)

router = Router()


class Onboarding(StatesGroup):
    waiting_for_name = State()
    waiting_for_birthdate = State()


class SettingsStates(StatesGroup):
    waiting_for_new_name = State()
    waiting_for_new_birthdate = State()


def get_main_keyboard():
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [
                types.KeyboardButton(text="🔮 Расклад"),
                types.KeyboardButton(text="🃏 Карта дня"),
            ],
            [
                types.KeyboardButton(text="❤️ На отношения"),
            ],
            [
                types.KeyboardButton(text="👤 Профиль"),
                types.KeyboardButton(text="💰 Баланс"),
            ],
            [
                types.KeyboardButton(text="⚙️ Настройки"),
            ],
        ],
        resize_keyboard=True
    )


def get_settings_keyboard():
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="✏️ Сменить имя")],
            [types.KeyboardButton(text="📅 Сменить дату рождения")],
            [types.KeyboardButton(text="🔙 Меню")],
        ],
        resize_keyboard=True
    )


@router.message(CommandStart())
async def start_handler(message: types.Message, state: FSMContext):
    await state.clear()

    user = await get_user(message.from_user.id)

    if user:
        await message.answer(
            f"С возвращением, {user.name} 🌙\n\n"
            "Что вас сегодня интересует?",
            reply_markup=get_main_keyboard()
        )
        return

    await message.answer(
        "🔮 Добро пожаловать.\n\n"
        "Вы на пороге пространства, где карты отражают не случайность,\n"
        "а тонкие линии вашей текущей реальности.\n\n"
        "Я помогу Вам увидеть:\n"
        "— скрытые ответы\n"
        "— внутренние состояния\n"
        "— возможные пути\n\n"
        "—\n\n"
        "✨ Вы можете задать вопрос\n"
        "или просто посмотреть, что сейчас происходит в Вашей жизни\n\n"
        "—\n\n"
        "Продолжая, Вы подтверждаете, что вам исполнилось 18 лет\n"
        "осознаете, что все ответы не являются рекомендациями\n"
        "и все решения Вы принимаете самостоятельно.\n\n"
        "Как я могу к Вам обращаться?",
        parse_mode="HTML"
    )

    await state.set_state(Onboarding.waiting_for_name)


@router.message(Onboarding.waiting_for_name)
async def get_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text.strip())

    await message.answer(
        "Введите вашу дату рождения в формате ДД.ММ.ГГГГ\n\n"
        "Например: 12.05.1995"
    )

    await state.set_state(Onboarding.waiting_for_birthdate)


@router.message(Onboarding.waiting_for_birthdate)
async def get_birthdate(message: types.Message, state: FSMContext):
    data = await state.get_data()

    name = data["name"]
    birthdate = message.text.strip()
    zodiac = calculate_zodiac(birthdate)

    await create_user(
        telegram_id=message.from_user.id,
        name=name,
        birthdate=birthdate,
        zodiac=zodiac
    )

    await state.clear()

    await message.answer(
        f"✨ Приятно познакомиться, {name}\n\n"
        f"Ваш знак: {zodiac}\n"
        f"🎁 Вам начислено 30 кредитов\n\n"
        "🔮 Можем начать работу с картами",
        reply_markup=get_main_keyboard()
    )


# ===================== ⚙️ НАСТРОЙКИ =====================

@router.message(F.text == "⚙️ Настройки")
async def settings_handler(message: types.Message, state: FSMContext):
    await state.clear()

    user = await get_user(message.from_user.id)

    await message.answer(
        f"⚙️ Настройки\n\n"
        f"Текущее имя: {user.name}\n"
        f"Текущая дата рождения: {user.birthdate}\n\n"
        f"Что хотите изменить?",
        reply_markup=get_settings_keyboard()
    )


@router.message(F.text == "✏️ Сменить имя")
async def settings_change_name_start(message: types.Message, state: FSMContext):
    await state.set_state(SettingsStates.waiting_for_new_name)

    await message.answer(
        "Введите новое имя:",
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=[[types.KeyboardButton(text="🔙 Меню")]],
            resize_keyboard=True
        )
    )


@router.message(SettingsStates.waiting_for_new_name, F.text & ~F.text.in_(["🔙 Меню"]))
async def settings_change_name_finish(message: types.Message, state: FSMContext):
    new_name = message.text.strip()

    await update_user_name(message.from_user.id, new_name)
    await state.clear()

    await message.answer(
        f"✅ Имя обновлено: {new_name}",
        reply_markup=get_settings_keyboard()
    )


@router.message(F.text == "📅 Сменить дату рождения")
async def settings_change_birthdate_start(message: types.Message, state: FSMContext):
    await state.set_state(SettingsStates.waiting_for_new_birthdate)

    await message.answer(
        "Введите новую дату рождения в формате ДД.ММ.ГГГГ\n\n"
        "Например: 12.05.1995",
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=[[types.KeyboardButton(text="🔙 Меню")]],
            resize_keyboard=True
        )
    )


@router.message(SettingsStates.waiting_for_new_birthdate, F.text & ~F.text.in_(["🔙 Меню"]))
async def settings_change_birthdate_finish(message: types.Message, state: FSMContext):
    new_birthdate = message.text.strip()
    zodiac = calculate_zodiac(new_birthdate)

    await update_user_birthdate(message.from_user.id, new_birthdate, zodiac)
    await state.clear()

    await message.answer(
        f"✅ Дата рождения обновлена: {new_birthdate}\n"
        f"Ваш знак: {zodiac}",
        reply_markup=get_settings_keyboard()
    )


def calculate_zodiac(date_str: str) -> str:
    try:
        day, month, _ = map(int, date_str.split("."))
    except:
        return "Неизвестно"

    zodiac_signs = [
        (20, "Козерог"), (19, "Водолей"), (20, "Рыбы"),
        (20, "Овен"), (21, "Телец"), (21, "Близнецы"),
        (22, "Рак"), (23, "Лев"), (23, "Дева"),
        (23, "Весы"), (22, "Скорпион"), (22, "Стрелец"),
        (31, "Козерог")
    ]

    if day < zodiac_signs[month - 1][0]:
        return zodiac_signs[month - 1][1]
    else:
        return zodiac_signs[month][1]