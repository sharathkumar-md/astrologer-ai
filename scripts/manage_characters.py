"""
Character Management Utility

Manage characters in the database.

Usage:
    python -m scripts.manage_characters list                    # List all characters
    python -m scripts.manage_characters list --all              # List all (including inactive)
    python -m scripts.manage_characters activate <character_id>  # Activate a character
    python -m scripts.manage_characters deactivate <character_id> # Deactivate a character
    python -m scripts.manage_characters export --output chars.csv # Export to CSV
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


def list_characters(show_all=False):
    """List all characters in database"""
    db = UserDatabase(DB_PATH)
    characters = db.get_all_characters(active_only=not show_all)

    if not characters:
        print("No characters found in database.")
        return

    print("\n" + "="*80)
    print(f"{'ID':<20} {'Name':<25} {'Emoji':<6} {'Active':<8} {'Experience':<10}")
    print("="*80)

    for char in characters:
        char_id = char['character_id']
        name = char['name']
        emoji = char.get('emoji', '✨')
        is_active = '✓ Yes' if char.get('is_active', 1) else '✗ No'
        exp = f"{char.get('experience', 0)} years" if char.get('experience') else 'N/A'

        print(f"{char_id:<20} {name:<25} {emoji:<6} {is_active:<8} {exp:<10}")

    print("="*80)
    print(f"Total: {len(characters)} character(s)")
    print()


def activate_character(character_id):
    """Activate a character"""
    db = UserDatabase(DB_PATH)

    if db.activate_character(character_id):
        logger.info(f"✓ Activated character: {character_id}")
        clear_character_cache()
        return True
    else:
        logger.error(f"✗ Failed to activate character: {character_id}")
        return False


def deactivate_character(character_id):
    """Deactivate a character"""
    db = UserDatabase(DB_PATH)

    if db.deactivate_character(character_id):
        logger.info(f"✓ Deactivated character: {character_id}")
        clear_character_cache()
        return True
    else:
        logger.error(f"✗ Failed to deactivate character: {character_id}")
        return False


def export_characters(output_path):
    """Export all characters to CSV"""
    db = UserDatabase(DB_PATH)
    characters = db.get_all_characters(active_only=False)

    if not characters:
        logger.warning("No characters to export")
        return False

    try:
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['character_id', 'name', 'emoji', 'about', 'age', 'experience', 'specialty', 'language_style']
            writer = csv.DictWriter(f, fieldnames=fieldnames)

            writer.writeheader()
            for char in characters:
                writer.writerow({
                    'character_id': char['character_id'],
                    'name': char['name'],
                    'emoji': char.get('emoji', '✨'),
                    'about': char.get('about', ''),
                    'age': char.get('age', ''),
                    'experience': char.get('experience', ''),
                    'specialty': char.get('specialty', ''),
                    'language_style': char.get('language_style', 'casual')
                })

        logger.info(f"✓ Exported {len(characters)} characters to: {output_path}")
        return True

    except Exception as e:
        logger.error(f"✗ Failed to export: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description='Manage characters in database')
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    # List command
    list_parser = subparsers.add_parser('list', help='List all characters')
    list_parser.add_argument('--all', action='store_true', help='Show inactive characters too')

    # Activate command
    activate_parser = subparsers.add_parser('activate', help='Activate a character')
    activate_parser.add_argument('character_id', help='Character ID to activate')

    # Deactivate command
    deactivate_parser = subparsers.add_parser('deactivate', help='Deactivate a character')
    deactivate_parser.add_argument('character_id', help='Character ID to deactivate')

    # Export command
    export_parser = subparsers.add_parser('export', help='Export characters to CSV')
    export_parser.add_argument('--output', required=True, help='Output CSV file path')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == 'list':
        list_characters(args.all)
    elif args.command == 'activate':
        success = activate_character(args.character_id)
        sys.exit(0 if success else 1)
    elif args.command == 'deactivate':
        success = deactivate_character(args.character_id)
        sys.exit(0 if success else 1)
    elif args.command == 'export':
        success = export_characters(args.output)
        sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
