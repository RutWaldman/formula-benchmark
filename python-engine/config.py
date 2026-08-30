"""
Configuration management for the Python Formula Engine.

This module provides centralized configuration for database connections
and other environment-specific settings.
"""

import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()


@dataclass
class DatabaseConfig:
    """Database connection configuration."""
    
    host: str
    port: int
    database: str
    user: str
    password: str
    
    @property
    def connection_string(self) -> str:
        """Generate PostgreSQL connection string."""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"
    
    @property
    def asyncpg_dsn(self) -> str:
        """Generate asyncpg-compatible DSN."""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"
    
    @classmethod
    def from_env(cls) -> "DatabaseConfig":
        """Create configuration from environment variables."""
        return cls(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", "5432")),
            database=os.getenv("DB_NAME", "formula_benchmark"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "postgres"),
        )


@dataclass
class EngineConfig:
    """Formula engine configuration."""
    
    engine_name: str = "Python_Eval"
    batch_size: int = 10000  # Number of records to process in each batch
    enable_logging: bool = True
    float_tolerance: float = 1e-9  # Tolerance for floating-point comparisons


@dataclass
class AppConfig:
    """Main application configuration."""
    
    database: DatabaseConfig
    engine: EngineConfig
    
    @classmethod
    def from_env(cls) -> "AppConfig":
        """Create full application configuration from environment."""
        return cls(
            database=DatabaseConfig.from_env(),
            engine=EngineConfig(
                engine_name=os.getenv("ENGINE_NAME", "Python_Eval"),
                batch_size=int(os.getenv("BATCH_SIZE", "10000")),
                enable_logging=os.getenv("ENABLE_LOGGING", "true").lower() == "true",
                float_tolerance=float(os.getenv("FLOAT_TOLERANCE", "1e-9")),
            ),
        )


# Global configuration instance
config: Optional[AppConfig] = None


def get_config() -> AppConfig:
    """Get or create the global configuration instance."""
    global config
    if config is None:
        config = AppConfig.from_env()
    return config


def reset_config() -> None:
    """Reset the global configuration (useful for testing)."""
    global config
    config = None
