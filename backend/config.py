"""Application configuration management."""
import os
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # App
    app_name: str = "AI Job Search Agent"
    app_version: str = "1.0.0"
    secret_key: str = "change-this-secret-key"

    # Database
    database_url: str = "sqlite:///./data/job_agent.db"

    # Server
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    allowed_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    # API Keys (can be set via .env or UI)
    openai_api_key: str = ""
    serpapi_key: str = ""

    # File storage
    upload_dir: str = "./uploads"
    generated_resumes_dir: str = "./generated_resumes"

    # Rate limiting
    job_search_delay: float = 1.0
    llm_request_delay: float = 0.5

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    @property
    def origins_list(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]


@lru_cache()
def get_settings() -> Settings:
    return Settings()
