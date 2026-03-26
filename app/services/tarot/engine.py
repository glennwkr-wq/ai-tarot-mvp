import random
from app.knowledge_base.cards import CARDS


def draw_cards(n: int = 3) -> list[dict]:
    return random.sample(CARDS, n)


def build_interpretation_context(cards: list[dict], question: str, mode: str = "general") -> str:
    if mode == "love":
        positions = ["Вы", "Партнер", "Динамика между вами"]
    elif mode == "career":
        positions = ["Текущая ситуация", "Возможности", "Куда двигаться"]
    elif mode == "daily":
        positions = ["Карта дня"]
    else:
        positions = ["Прошлое", "Настоящее", "Будущее"]

    lines = []

    for i, card in enumerate(cards):
        position = positions[i] if i < len(positions) else f"Карта {i+1}"

        lines.append(
            f"""
[{position}] {card['name']}

Ключевые слова: {", ".join(card['keywords'])}

Общее:
{card['general']}

Любовь:
{card['love']}

Карьера:
{card['career']}

О себе:
{card['self']}

Совет:
{card['advice']}
"""
        )

    return f"""
Вопрос пользователя:
{question}

Режим:
{mode}

Карты:
{''.join(lines)}
"""