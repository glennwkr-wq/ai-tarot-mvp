from openai import OpenAI
from app.core.config import settings
from app.services.tarot.engine import build_interpretation_context

client = OpenAI(api_key=settings.OPENAI_API_KEY)


async def generate_tarot_answer(question: str, cards: list[dict]) -> str:
    context = build_interpretation_context(cards, question)

    prompt = f"""
Ты опытный таролог.

Твоя задача — сделать интерпретацию ТОЛЬКО на основе переданных значений карт.

❗ ВАЖНО:
- не придумывай значения карт
- не добавляй эзотерический мусор
- не давай категоричных предсказаний
- говори мягко и уважительно

СТИЛЬ:
- спокойный
- немного мистический
- как живой человек
- без пафоса и воды

СТРУКТУРА:

🔮 Расклад

🌒 Прошлое — карта
⚡ Настоящее — карта
🌕 Будущее — карта

🧭 Вывод:
кратко и по делу (1-2 абзаца)

КОНТЕКСТ:
{context}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=300,  # 👈 важно
        temperature=0.8,
    )

    return response.choices[0].message.content