from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    BOT_TOKEN: str
    OPENAI_API_KEY: str

    # 👇 добавляем админа
    ADMIN_ID: int = 1120321526  # сюда вставишь свой Telegram ID

    class Config:
        env_file = ".env"


settings = Settings()