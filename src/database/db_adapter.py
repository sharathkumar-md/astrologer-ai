"""
Database Adapter - REMOVED

NOTE: Database functionality has been removed from this project.
All user/birth data is now provided by AstroVoice integration via API requests.
See /docs/ASTROVOICE_API.md for the API documentation.

The /api/v1/chat endpoint receives birth data directly in the request body.
"""

from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class DatabaseRemovedError(Exception):
    """Raised when trying to use removed database functionality"""
    pass


def get_database():
    """
    DEPRECATED: Database removed from project.

    Raises:
        DatabaseRemovedError: Always raised - use /api/v1/chat with birth data in request
    """
    raise DatabaseRemovedError(
        "Database has been removed from this project. "
        "Use /api/v1/chat endpoint with birth data in request body. "
        "See /docs/ASTROVOICE_API.md for API documentation."
    )


def get_db_instance():
    """
    DEPRECATED: Database removed from project.

    Raises:
        DatabaseRemovedError: Always raised - use /api/v1/chat with birth data in request
    """
    raise DatabaseRemovedError(
        "Database has been removed from this project. "
        "Use /api/v1/chat endpoint with birth data in request body. "
        "See /docs/ASTROVOICE_API.md for API documentation."
    )
