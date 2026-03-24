from app.services.tarot.engine import build_interpretation_context
from app.core.config import settings
from openai import OpenAI

client = OpenAI(api_key=settings.OPENAI_API_KEY)


async def generate_tarot_answer(question: str, cards: list[dict]) -> str:
    context = build_interpretation_context(cards, question)

    prompt = f"""
Ты профессиональный таролог.

Ты НЕ придумываешь значения карт.
Ты работаешь ТОЛЬКО с данными, которые переданы.

Твоя задача:
объединить значения карт в связный расклад.

СТИЛЬ:
- спокойный
- мягкий
- немного мистический
- без категоричных предсказаний

СТРУКТУРА:

🔮 Расклад

🌒 Прошлое
⚡ Настоящее
🌕 Будущее

🧭 Вывод:
1-2 абзаца

ВАЖНО:
- используй только переданные значения
- не выдумывай символику
- адаптируй под вопрос
- не делай длинный текст

КОНТЕКСТ:
{context}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=300,
        temperature=0.7,
    )

    return response.choices[0].message.content