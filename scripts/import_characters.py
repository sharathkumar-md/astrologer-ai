"""
CSV Character Import Utility

Import character data from CSV file into the database.

Usage:
    python -m scripts.import_characters --csv characters.csv
    python -m scripts.import_characters --csv characters.csv --update  # Update existing characters
"""

import argparse
import csv
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.database import UserDatabase
from src.utils.characters import clear_character_cache
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

# Database path
DB_PATH = os.path.join(os.getcwd(), 'astra.db')


def validate_csv_row(row, line_number):
    """Validate a CSV row has required fields"""
    required_fields = ['character_id', 'name']
    missing = [field for field in required_fields if not row.get(field)]

    if missing:
        logger.error(f"Line {line_number}: Missing required fields: {', '.join(missing)}")
        return False

    # Validate character_id format (lowercase, no spaces, alphanumeric + underscores)
    char_id = row['character_id'].strip()
    if not char_id.replace('_', '').isalnum():
        logger.error(f"Line {line_number}: Invalid character_id '{char_id}'. Use alphanumeric characters and underscores only.")
        return False

    return True


def import_characters_from_csv(csv_path, update_existing=False):
    """
    Import characters from CSV file into database

    Args:
        csv_path: Path to CSV file
        update_existing: If True, update existing characters. If False, skip them.

    Returns:
        Tuple of (success_count, skip_count, error_count)
    """
    if not os.path.exists(csv_path):
        logger.error(f"CSV file not found: {csv_path}")
        return (0, 0, 1)

    db = UserDatabase(DB_PATH)

    success_count = 0
    skip_count = 0
    error_count = 0

    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            # Validate CSV has required columns
            required_columns = ['character_id', 'name']
            if not all(col in reader.fieldnames for col in required_columns):
                logger.error(f"CSV must have columns: {', '.join(required_columns)}")
                logger.error(f"Found columns: {', '.join(reader.fieldnames)}")
                return (0, 0, 1)

            logger.info(f"Importing characters from: {csv_path}")
            logger.info(f"Update mode: {update_existing}")
            logger.info("-" * 60)

            for line_num, row in enumerate(reader, start=2):  # Start at 2 (header is line 1)
                # Validate row
                if not validate_csv_row(row, line_num):
                    error_count += 1
                    continue

                # Extract and clean data
                character_id = row['character_id'].strip().lower()
                name = row['name'].strip()
                emoji = row.get('emoji', '✨').strip() or '✨'
                about = row.get('about', '').strip() or None
                specialty = row.get('specialty', '').strip() or None
                language_style = row.get('language_style', 'casual').strip().lower()

                # Parse integers
                try:
                    age = int(row['age']) if row.get('age', '').strip() else None
                except ValueError:
                    logger.warning(f"Line {line_num}: Invalid age value, skipping age")
                    age = None

                try:
                    experience = int(row['experience']) if row.get('experience', '').strip() else None
                except ValueError:
                    logger.warning(f"Line {line_num}: Invalid experience value, skipping experience")
                    experience = None

                # Check if character exists
                existing = db.get_character(character_id)

                if existing:
                    if update_existing:
                        # Update existing character
                        updated = db.update_character(
                            character_id,
                            name=name,
                            emoji=emoji,
                            about=about,
                            age=age,
                            experience=experience,
                            specialty=specialty,
                            language_style=language_style
                        )
                        if updated:
                            logger.info(f"✓ Updated: {character_id} - {name}")
                            success_count += 1
                        else:
                            logger.error(f"✗ Failed to update: {character_id}")
                            error_count += 1
                    else:
                        logger.info(f"⊘ Skipped (exists): {character_id} - {name}")
                        skip_count += 1
                else:
                    # Add new character
                    added = db.add_character(
                        character_id=character_id,
                        name=name,
                        emoji=emoji,
                        about=about,
                        age=age,
                        experience=experience,
                        specialty=specialty,
                        language_style=language_style
                    )
                    if added:
                        logger.info(f"✓ Added: {character_id} - {name}")
                        success_count += 1
                    else:
                        logger.error(f"✗ Failed to add: {character_id}")
                        error_count += 1

    except Exception as e:
        logger.error(f"Error reading CSV: {e}")
        return (success_count, skip_count, error_count + 1)

    # Clear character cache so new characters are loaded
    clear_character_cache()

    logger.info("-" * 60)
    logger.info(f"Import complete:")
    logger.info(f"  ✓ Success: {success_count}")
    logger.info(f"  ⊘ Skipped: {skip_count}")
    logger.info(f"  ✗ Errors:  {error_count}")

    return (success_count, skip_count, error_count)


def main():
    parser = argparse.ArgumentParser(description='Import characters from CSV into database')
    parser.add_argument('--csv', required=True, help='Path to CSV file')
    parser.add_argument('--update', action='store_true', help='Update existing characters')

    args = parser.parse_args()

    success, skipped, errors = import_characters_from_csv(args.csv, args.update)

    # Exit with error code if there were errors
    if errors > 0:
        sys.exit(1)


if __name__ == '__main__':
    main()
