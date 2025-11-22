#!/usr/bin/env python3
"""
Database migration script for AutoCTF
Adds new fields for enhanced SQLi exploitation features
"""

import sys
import os

# Add dashboard backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'dashboard', 'backend'))

from sqlalchemy import text
from database import engine, SessionLocal

def run_migration():
    """Run database migration to add new vulnerability fields"""

    print("🔄 Running AutoCTF database migration...")
    print("Adding fields: dump_data, cvss_score, title, proof")

    migrations = [
        # Add dump_data column (JSON)
        """
        ALTER TABLE vulnerabilities
        ADD COLUMN IF NOT EXISTS dump_data JSON;
        """,

        # Add cvss_score column
        """
        ALTER TABLE vulnerabilities
        ADD COLUMN IF NOT EXISTS cvss_score VARCHAR(10);
        """,

        # Add title column
        """
        ALTER TABLE vulnerabilities
        ADD COLUMN IF NOT EXISTS title VARCHAR(255);
        """,

        # Add proof column
        """
        ALTER TABLE vulnerabilities
        ADD COLUMN IF NOT EXISTS proof TEXT;
        """,
    ]

    try:
        with engine.connect() as conn:
            for i, migration in enumerate(migrations, 1):
                print(f"  [{i}/{len(migrations)}] Applying migration...")
                conn.execute(text(migration))
                conn.commit()

        print("✅ Migration completed successfully!")
        print("\nNew vulnerability table schema:")
        print("  - dump_data (JSON): Store DB dump results")
        print("  - cvss_score (VARCHAR): CVSS vulnerability score")
        print("  - title (VARCHAR): Vulnerability title")
        print("  - proof (TEXT): Proof of exploitation")

        return True

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        print("\nTroubleshooting:")
        print("1. Check if columns already exist")
        print("2. Verify database connection in .env")
        print("3. For SQLite, columns might need manual addition")
        print("\nSQLite Manual Migration:")
        print("  The script above uses PostgreSQL syntax.")
        print("  For SQLite, you may need to recreate the table.")
        print("  Backup your data first!")

        return False


def check_migration_status():
    """Check if migration has been applied"""

    print("🔍 Checking migration status...")

    try:
        with engine.connect() as conn:
            # Try to query new columns
            result = conn.execute(text("""
                SELECT dump_data, cvss_score, title, proof
                FROM vulnerabilities
                LIMIT 0
            """))

            print("✅ Migration appears to be applied")
            print("   All new columns exist in vulnerabilities table")
            return True

    except Exception as e:
        print("⚠️  Migration not yet applied")
        print(f"   Error: {e}")
        return False


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="AutoCTF Database Migration")
    parser.add_argument('--check', action='store_true', help='Check migration status')
    parser.add_argument('--apply', action='store_true', help='Apply migration')

    args = parser.parse_args()

    if args.check:
        check_migration_status()
    elif args.apply:
        run_migration()
    else:
        print("AutoCTF Database Migration Tool")
        print("\nUsage:")
        print("  python migrate_db.py --check   Check if migration is needed")
        print("  python migrate_db.py --apply   Apply the migration")
        print("\nIMPORTANT: Backup your database before running migration!")
