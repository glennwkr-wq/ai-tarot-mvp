from aiogram import Router, types, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

router = Router()


# ===== FSM состояния =====
class Onboarding(StatesGroup):
    waiting_for_name = State()
    waiting_for_birthdate = State()


# ===== временное хранилище (пока без БД) =====
users = {}


# ===== клавиатура =====
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
                types.KeyboardButton(text="👤 Профиль"),
            ],
            [
                types.KeyboardButton(text="💰 Баланс"),
                types.KeyboardButton(text="⚙️ Настройки"),
            ],
        ],
        resize_keyboard=True
    )


# ===== старт =====
@router.message(CommandStart())
async def start_handler(message: types.Message, state: FSMContext):
    user_id = message.from_user.id

    # если пользователь уже есть → меню
    if user_id in users:
        await message.answer(
            f"С возвращением, {users[user_id]['name']} 🌙\n\n"
            "Что вас сегодня интересует?",
            reply_markup=get_main_keyboard()
        )
        return

    # onboarding старт
    await message.answer(
        "🔮 <b>AI Таролог</b>\n\n"
        "Перед началом важно:\n"
        "— Я не даю точных предсказаний будущего\n"
        "— Я не заменяю врача, юриста или психолога\n"
        "— Все ответы носят интерпретационный характер\n\n"
        "✨ Продолжая, вы подтверждаете, что вам есть 18 лет\n\n"
        "Как я могу к вам обращаться?",
        parse_mode="HTML"
    )

    await state.set_state(Onboarding.waiting_for_name)


# ===== имя =====
@router.message(Onboarding.waiting_for_name)
async def get_name(message: types.Message, state: FSMContext):
    name = message.text.strip()

    await state.update_data(name=name)

    await message.answer(
        "Введите вашу дату рождения в формате ДД.ММ.ГГГГ\n\n"
        "Например: 12.05.1995"
    )

    await state.set_state(Onboarding.waiting_for_birthdate)


# ===== дата рождения =====
@router.message(Onboarding.waiting_for_birthdate)
async def get_birthdate(message: types.Message, state: FSMContext):
    birthdate = message.text.strip()

    data = await state.get_data()
    name = data["name"]

    zodiac = calculate_zodiac(birthdate)

    user_id = message.from_user.id

    users[user_id] = {
        "name": name,
        "birthdate": birthdate,
        "zodiac": zodiac,
        "balance": 10  # стартовые кредиты
    }

    await state.clear()

    await message.answer(
        f"✨ Приятно познакомиться, {name}\n\n"
        f"Ваш знак: {zodiac}\n"
        f"🎁 Вам начислено 10 кредитов\n\n"
        "🔮 Можем начать работу с картами",
        reply_markup=get_main_keyboard()
    )


# ===== зодиак =====
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