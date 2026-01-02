"""
Initialize PostgreSQL database with schema
Run this ONCE after creating Render database
"""

from src.utils import config
from src.database.pg_database import PostgreSQLDatabase

from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def main():
    """Initialize PostgreSQL database"""

    if not config.DATABASE_URL:
        logger.error("DATABASE_URL not found in environment variables")
        logger.info("  Please add DATABASE_URL to your .env file")
        logger.info("  Example: DATABASE_URL=postgresql://user:password@host:5432/database")
        return

    logger.info("Initializing PostgreSQL database...")
    logger.info("Using database: {config.DATABASE_URL.split('@')[1] if '@' in config.DATABASE_URL else 'hidden'}")

    try:
        # Create database connection
        db = PostgreSQLDatabase(config.DATABASE_URL)

        # Initialize schema
        db.init_db()

        logger.info("\n[OK] Database initialized successfully!")
        logger.info("\nNext steps:")
        logger.info("1. Update .env: Set USE_POSTGRESQL=true")
        logger.info("2. Run migration: python migrate_to_postgres.py")
        logger.info("3. Test connection: python test_db.py")

        db.close()

    except Exception as e:
        logger.info("\n[ERROR] Database initialization failed: {e}")
        logger.info("\nTroubleshooting:")
        logger.info("- Check if DATABASE_URL is correct")
        logger.info("- Ensure Render database is created and running")
        logger.info("- Verify your IP is allowed to connect (Render allows all by default)")

if __name__ == "__main__":
    main()
