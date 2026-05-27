from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    api_key: str
    database_url: str = "sqlite:///./app.db"
    log_level: str = "INFO"
    loads_csv_path: str = "app/data/loads.csv"
    seed_demo_data: bool = False

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
