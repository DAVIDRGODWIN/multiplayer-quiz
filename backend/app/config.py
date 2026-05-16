from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://quiz:quiz@localhost:5432/quiz"
    redis_url: str = "redis://localhost:6379"
    secret_key: str = "change-me-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    internal_secret: str = "change-me-in-production"


settings = Settings()
