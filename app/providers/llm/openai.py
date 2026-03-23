from openai import OpenAI
from app.core.config import settings
from app.services.tarot.engine import build_interpretation_context

client = OpenAI(api_key=settings.OPENAI_API_KEY)


async def generate_tarot_answer(question: str, cards: list[dict]) -> str:
    context = build_interpretation_context(cards, question)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Ты профессиональный таролог."},
            {"role": "user", "content": context},
        ],
        max_tokens=300,
        temperature=0.8,
    )

    return response.choices[0].message.content