from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    api_key: str
    fmcsa_webkey: str = ""
    database_url: str = "sqlite:///./app.db"
    log_level: str = "INFO"
    environment: str = "development"
    allow_mock_fmcsa: bool = False
    loads_csv_path: str = "app/data/loads.csv"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
