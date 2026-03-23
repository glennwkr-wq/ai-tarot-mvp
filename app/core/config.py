import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    DATABASE_URL = os.getenv("DATABASE_URL")

settings = Settings()

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    BOT_TOKEN: str
    OPENAI_API_KEY: str

    class Config:
        env_file = ".env"


settings = Settings()