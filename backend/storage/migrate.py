"""Simple database migration runner (Flyway-inspired)."""
import aiosqlite
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

MIGRATIONS_DIR = Path(__file__).parent / "migrations"

async def run_migrations(db_path: str) -> None:
    """Apply any pending SQL migrations in order."""
    async with aiosqlite.connect(db_path) as db:
        # Create migrations tracking table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version TEXT PRIMARY KEY,
                applied_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()

        # Get applied migrations
        async with db.execute("SELECT version FROM schema_migrations") as cursor:
            applied = {row[0] for row in await cursor.fetchall()}

        # Find and sort migration files (V1__, V2__, etc.)
        migration_files = sorted(MIGRATIONS_DIR.glob("V*.sql"))

        for migration_file in migration_files:
            version = migration_file.stem  # e.g. "V1__initial_schema"
            if version in applied:
                continue

            logger.info(f"Applying migration: {version}")
            sql = migration_file.read_text()

            # Execute each statement
            for statement in sql.split(";"):
                statement = statement.strip()
                if statement:
                    await db.execute(statement)

            await db.execute(
                "INSERT INTO schema_migrations (version) VALUES (?)", (version,)
            )
            await db.commit()
            logger.info(f"Applied migration: {version}")
