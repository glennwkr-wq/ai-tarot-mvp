from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    BOT_TOKEN: str
    OPENAI_API_KEY: str

    ADMIN_ID: int = 1120321526

    # 👇 готовим под Postgres (Neon)
    DATABASE_URL: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )


settings = Settings()