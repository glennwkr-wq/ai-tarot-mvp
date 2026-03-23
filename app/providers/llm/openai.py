from openai import OpenAI
from app.core.config import settings
from app.services.tarot.engine import build_interpretation_context

client = OpenAI(api_key=settings.OPENAI_API_KEY)


async def generate_tarot_answer(question: str, cards: list[dict]) -> str:
    context = build_interpretation_context(cards, question)

    prompt = f"""
Ты профессиональный таролог.

Дай глубокий, но понятный расклад.

СТИЛЬ:
- живой, как человек
- немного мистический
- без банальностей
- без "воды"
- без категоричных предсказаний

СТРУКТУРА ОБЯЗАТЕЛЬНА:

# 🔮 Расклад

## 🌒 Прошлое — [название карты]
(интерпретация)

## ⚡ Настоящее — [название карты]
(интерпретация)

## 🌕 Будущее — [название карты]
(интерпретация)

---

## 🧭 Вывод
(1-2 абзаца: суть + совет)

ВАЖНО:
- используй значения карт из контекста
- адаптируй под вопрос
- не выдумывай значения
- пиши естественно

КОНТЕКСТ:
{context}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": prompt}
        ],
        max_tokens=500,
        temperature=0.9,
    )

    return response.choices[0].message.content