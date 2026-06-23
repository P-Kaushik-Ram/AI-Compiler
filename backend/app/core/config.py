"""Application configuration using Pydantic settings."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    PROJECT_NAME: str = "AI Compiler"
    VERSION: str = "0.1.0"


settings = Settings()
