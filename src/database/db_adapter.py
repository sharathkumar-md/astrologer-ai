"""
Unified Database Adapter
Automatically uses PostgreSQL or SQLite based on config
"""

from src.utils import config
from src.database.database import UserDatabase
from src.database.pg_database import PostgreSQLDatabase

from src.utils.logger import setup_logger

logger = setup_logger(__name__)



def get_database():
    """
    Get database instance based on configuration

    Returns:
        Database instance (PostgreSQL or SQLite)
    """

    if config.USE_POSTGRESQL and config.DATABASE_URL:
        # Use PostgreSQL
        logger.info("Using PostgreSQL")
        return PostgreSQLDatabase(config.DATABASE_URL)
    else:
        # Fallback to SQLite
        logger.info("Using SQLite (fallback)")
        return UserDatabase(config.DB_NAME)


# Singleton instance
_db_instance = None


def get_db_instance():
    """Get or create singleton database instance"""
    global _db_instance

    if _db_instance is None:
        _db_instance = get_database()

    return _db_instance
