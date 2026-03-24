import random
from app.knowledge_base.cards import CARDS


def draw_cards(n: int = 3) -> list[dict]:
    return random.sample(CARDS, n)


def build_interpretation_context(cards: list[dict], question: str) -> str:
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

Совет:
{card['advice']}
"""
        )

    return f"""
Вопрос пользователя:
{question}

Карты:
{''.join(lines)}
"""