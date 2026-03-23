import random
from app.knowledge_base.cards import CARDS


def draw_cards(n: int = 3) -> list[dict]:
    return random.sample(CARDS, n)


def build_interpretation_context(cards: list[dict], question: str) -> str:
    return f"""
Вопрос пользователя:
{question}

Карты:
{chr(10).join([f"{c['name']}: {c['meaning']}" for c in cards])}

Сделай интерпретацию, опираясь только на значения карт.
Не придумывай новые значения.
"""