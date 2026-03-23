from openai import OpenAI
from app.core.config import settings

client = OpenAI(api_key=settings.OPENAI_API_KEY)


def generate_tarot_reading(cards: list[str], question: str) -> str:
    prompt = f"""
Ты таролог. Дай краткое, понятное и мистическое толкование.

Вопрос пользователя:
{question}

Карты:
{", ".join(cards)}

Ответ:
- не более 5-6 предложений
- без воды
- конкретно по ситуации
"""

    response = client.chat.completions.create(
        model="gpt-5.4-mini",
        messages=[
            {"role": "user", "content": prompt}
        ],
        max_tokens=300,
        temperature=0.8,
    )

    return response.choices[0].message.content