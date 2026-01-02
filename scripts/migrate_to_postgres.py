"""
Migrate data from SQLite to PostgreSQL
Run this AFTER initializing PostgreSQL schema
"""

from src.utils import config
from src.database.database import UserDatabase  # SQLite
from src.database.pg_database import PostgreSQLDatabase  # PostgreSQL
import json
from datetime import datetime

from src.utils.logger import setup_logger

logger = setup_logger(__name__)



def migrate_users(sqlite_db, pg_db):
    """Migrate all users from SQLite to PostgreSQL"""

    logger.info("\n[DATA] Migrating users...")

    users = sqlite_db.list_users()

    if not users:
        logger.info("  [INFO]  No users found in SQLite database")
        return {}

    user_id_mapping = {}  # Old ID -> New ID

    for old_user in users:
        user_id = old_user[0]

        # Get full user data
        full_user = sqlite_db.get_user(user_id)

        if not full_user:
            continue

        # Extract user data
        (_, name, birth_date, birth_time, birth_location,
         latitude, longitude, timezone, natal_chart_json, created_at) = full_user

        # Parse natal chart
        natal_chart = json.loads(natal_chart_json) if natal_chart_json else {}

        try:
            # Add to PostgreSQL
            new_user_id = pg_db.add_user(
                name=name,
                birth_date=birth_date,  # Already in DD/MM/YYYY format
                birth_time=birth_time,
                birth_location=birth_location,
                latitude=latitude,
                longitude=longitude,
                timezone=timezone,
                natal_chart=natal_chart
            )

            user_id_mapping[user_id] = new_user_id
            logger.info("  [OK] Migrated user: {name} (ID: {user_id} -> {new_user_id})")

        except Exception as e:
            logger.info("  [ERROR] Failed to migrate user {name}: {e}")

    logger.info("\n[OK] Migrated {len(user_id_mapping)} users")
    return user_id_mapping


def migrate_conversations(sqlite_db, pg_db, user_id_mapping):
    """Migrate conversations from SQLite to PostgreSQL"""

    logger.info("\n[CONV] Migrating conversations...")

    total_conversations = 0

    for old_user_id, new_user_id in user_id_mapping.items():
        # Get conversation history for this user
        history = sqlite_db.get_conversation_history(old_user_id, limit=1000)

        if not history:
            continue

        # Group messages into user/assistant pairs
        # history format: [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]

        session_id = f"migrated_session_{new_user_id}_{datetime.now().strftime('%Y%m%d')}"

        # Extract query/response pairs
        i = 0
        while i < len(history) - 1:
            if history[i]["role"] == "user" and history[i + 1]["role"] == "assistant":
                query = history[i]["content"]
                response = history[i + 1]["content"]

                try:
                    pg_db.add_conversation(
                        user_id=new_user_id,
                        query=query,
                        response=response,
                        session_id=session_id
                    )
                    total_conversations += 1
                except Exception as e:
                    logger.info("  [ERROR] Failed to migrate conversation: {e}")

                i += 2
            else:
                i += 1

    logger.info("Migrated {total_conversations} conversations")


def verify_migration(sqlite_db, pg_db, user_id_mapping):
    """Verify migration was successful"""

    logger.info("\n[CHECK] Verifying migration...")

    # Check user count
    sqlite_users = len(sqlite_db.list_users())
    postgres_users = len(pg_db.list_users())

    logger.info("  Users: SQLite={sqlite_users}, PostgreSQL={postgres_users}")

    if sqlite_users == postgres_users:
        logger.info("  [OK] User count matches")
    else:
        logger.info("  [WARNING]  User count mismatch!")

    # Check a sample user
    if user_id_mapping:
        old_id = list(user_id_mapping.keys())[0]
        new_id = user_id_mapping[old_id]

        sqlite_user = sqlite_db.get_user(old_id)
        pg_user = pg_db.get_user(new_id)

        if sqlite_user and pg_user:
            logger.info("  [OK] Sample user verified: {sqlite_user[1]} (ID: {old_id} -> {new_id})")
        else:
            logger.info("  [ERROR] Sample user verification failed")

    logger.info("\n[OK] Migration verification complete")


def main():
    """Main migration function"""

    print("=" * 60)
    logger.info("ASTRA Database Migration: SQLite -> PostgreSQL")
    print("=" * 60)

    # Check environment
    if not config.DATABASE_URL:
        logger.info("\n[ERROR] DATABASE_URL not found in environment variables")
        logger.info("  Please add DATABASE_URL to your .env file")
        return

    if not config.USE_POSTGRESQL:
        logger.info("\n[WARNING]  WARNING: USE_POSTGRESQL is set to 'false'")
        logger.info("  Set USE_POSTGRESQL=true in .env after migration")

    # Connect to databases
    logger.info("\n[CONN] Connecting to databases...")

    try:
        sqlite_db = UserDatabase(config.DB_NAME)
        logger.info("  [OK] Connected to SQLite: {config.DB_NAME}")

        pg_db = PostgreSQLDatabase(config.DATABASE_URL)
        logger.info("  [OK] Connected to PostgreSQL")

    except Exception as e:
        logger.info("  [ERROR] Connection failed: {e}")
        return

    # Confirm migration
    logger.info("\n[WARNING]  This will copy all data from SQLite to PostgreSQL")
    logger.info("  Your SQLite database will NOT be deleted (safe backup)")
    response = input("\nProceed with migration? (yes/no): ")

    if response.lower() not in ['yes', 'y']:
        logger.info("Migration cancelled")
        return

    # Perform migration
    try:
        # Migrate users
        user_id_mapping = migrate_users(sqlite_db, pg_db)

        # Migrate conversations
        if user_id_mapping:
            migrate_conversations(sqlite_db, pg_db, user_id_mapping)

        # Verify migration
        verify_migration(sqlite_db, pg_db, user_id_mapping)

        print("\n" + "=" * 60)
        logger.info("MIGRATION COMPLETE!")
        print("=" * 60)
        logger.info("\nNext steps:")
        logger.info("1. Update .env: Set USE_POSTGRESQL=true")
        logger.info("2. Restart your application")
        logger.info("3. Test with a sample query")
        logger.info("4. Keep {config.DB_NAME} as backup (don't delete it yet)")

        pg_db.close()

    except Exception as e:
        logger.info("\n[ERROR] Migration failed: {e}")
        logger.info("\nYour SQLite database is unchanged. Safe to retry.")


if __name__ == "__main__":
    main()
