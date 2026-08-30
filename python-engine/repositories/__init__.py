"""
Repository package for database access.

This package contains repository classes that handle all database
operations including reading data, saving results, and logging.
"""

from .postgres_repository import PostgresRepository

__all__ = ["PostgresRepository"]
