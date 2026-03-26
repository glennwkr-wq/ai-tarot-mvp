from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    BOT_TOKEN: str
    OPENAI_API_KEY: str

    # Можно хранить несколько ID через запятую
    ADMIN_ID: str = "1120321526,757091056"

    # 👇 ДОБАВЛЕНО: отдельный админ для поддержки
    SUPPORT_ADMIN_ID: int

    # 👇 готовим под Postgres (Neon)
    DATABASE_URL: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )

    @property
    def admin_ids(self) -> list[int]:
        return [int(x.strip()) for x in self.ADMIN_ID.split(",") if x.strip()]


settings = Settings()