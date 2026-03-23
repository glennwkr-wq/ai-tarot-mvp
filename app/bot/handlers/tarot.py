from aiogram import Router, types
import random

router = Router()

cards = [
    "Шут", "Маг", "Жрица", "Императрица", "Император",
    "Иерофант", "Влюбленные", "Колесница", "Сила", "Отшельник",
    "Колесо фортуны", "Справедливость", "Повешенный", "Смерть",
    "Умеренность", "Дьявол", "Башня", "Звезда", "Луна", "Солнце",
    "Суд", "Мир"
]


def generate_interpretation(selected_cards):
    return (
        f"🔮 Ваш расклад:\n\n"
        f"1. {selected_cards[0]}\n"
        f"2. {selected_cards[1]}\n"
        f"3. {selected_cards[2]}\n\n"
        f"✨ Общий смысл:\n"
        f"Вы находитесь в процессе изменений. Карты указывают, "
        f"что важно доверять себе и не бояться действовать."
    )


@router.message(lambda message: message.text == "🔮 Сделать расклад")
async def tarot_handler(message: types.Message):
    selected = random.sample(cards, 3)

    await message.answer("🔮 Я тяну карты...")

    await message.answer(generate_interpretation(selected))


@router.message(lambda message: message.text == "🃏 Карта дня")
async def card_of_day(message: types.Message):
    card = random.choice(cards)

    await message.answer(
        f"🃏 Ваша карта дня: {card}\n\n"
        f"Сегодня эта карта говорит о внутреннем фокусе и внимании к себе."
    )


@router.message(lambda message: message.text == "💰 Баланс")
async def balance(message: types.Message):
    await message.answer(
        "💰 Ваш баланс: 5 кредитов\n\n"
        "Пока что это заглушка — скоро подключим оплату."
    )