"""
Database modules for ASTRA - REMOVED

NOTE: Database functionality has been removed from this project.
All user/birth data is now provided by AstroVoice integration via API requests.
See /docs/ASTROVOICE_API.md for the API documentation.

The /api/v1/chat endpoint receives birth data directly in the request body.
"""

from .db_adapter import get_db_instance, get_database, DatabaseRemovedError

__all__ = ['get_db_instance', 'get_database', 'DatabaseRemovedError']
