"""
Configuration management for the FastAPI backend.

Handles database connection settings and application configuration
using environment variables with sensible defaults for local development.
"""

import os
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    app_name: str = "Formula Benchmark API"
    app_version: str = "1.0.0"
    debug: bool = False

    # Database Connection - can be overridden by DATABASE_URL env var
    database_url: str | None = None
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "formula_benchmark"
    db_user: str = "benchmark_user"
    db_password: str = "benchmark_pass"

    # Database Pool Settings
    db_min_pool_size: int = 5
    db_max_pool_size: int = 20

    # CORS Settings
    cors_origins: list[str] = ["*"]
    cors_allow_credentials: bool = True
    cors_allow_methods: list[str] = ["*"]
    cors_allow_headers: list[str] = ["*"]

    @property
    def get_database_url(self) -> str:
        """Construct PostgreSQL connection URL."""
        if self.database_url:
            return self.database_url
        return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    @property
    def async_database_url(self) -> str:
        """Construct asyncpg connection URL."""
        return self.get_database_url

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached application settings.

    Uses lru_cache to ensure settings are only loaded once,
    improving performance and ensuring consistency.
    """
    return Settings()


# Global settings instance for convenience
settings = get_settings()
