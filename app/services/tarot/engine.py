import random
from app.knowledge_base.cards import CARDS


def draw_cards(count: int = 3):
    selected = random.sample(CARDS, count)

    result = []
    for card in selected:
        reversed_flag = random.choice([True, False])

        result.append({
            "name": card["name"],
            "meaning": card["meaning"],
            "reversed": reversed_flag
        })

    return result