import os
import sqlite3
from dotenv import load_dotenv

# Try to import psycopg2 for PostgreSQL handling
try:
    import psycopg2
except ImportError:
    print("Error: 'psycopg2-binary' is not installed.")
    print("Please run: pip install psycopg2-binary")
    exit(1)

# Load environment variables from your .env file
load_dotenv()

SQLITE_DB = os.getenv("DB_PATH", "./database.db")
POSTGRES_URL = os.getenv("DATABASE_URL")

if not POSTGRES_URL:
    print("Error: DATABASE_URL is missing from your .env file!")
    exit(1)


def migrate():
    print("🔄 Connecting to databases...")
    sqlite_conn = sqlite3.connect(SQLITE_DB)
    sqlite_cursor = sqlite_conn.cursor()

    try:
        pg_conn = psycopg2.connect(POSTGRES_URL)
        pg_cursor = pg_conn.cursor()
    except Exception as e:
        print(f"❌ Failed to connect to Supabase: {e}")
        return

    # 1. Fetch all user tables from SQLite
    sqlite_cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';"
    )
    tables = [row[0] for row in sqlite_cursor.fetchall()]

    print(f"📦 Found tables to migrate: {tables}")

    for table in tables:
        print(f"\n⏳ Migrating table: '{table}'...")

        # 2. Get column names from the SQLite table
        sqlite_cursor.execute(f"PRAGMA table_info({table});")
        columns = [row[1] for row in sqlite_cursor.fetchall()]

        # 3. Extract all rows from SQLite
        sqlite_cursor.execute(f"SELECT * FROM {table};")
        rows = sqlite_cursor.fetchall()

        if not rows:
            print(f"ℹ️ Table '{table}' is empty. Skipping rows.")
            continue

        # 4. Map the data over to Supabase
        col_names = ", ".join([f'"{col}"' for col in columns])
        placeholders = ", ".join(["%s"] * len(columns))

        # "ON CONFLICT DO NOTHING" prevents crashes if you run the script twice
        insert_query = (
            f"INSERT INTO {table} ({col_names}) VALUES ({placeholders}) ON CONFLICT DO NOTHING;"
        )

        try:
            pg_cursor.executemany(insert_query, rows)
            pg_conn.commit()
            print(f"✅ Successfully transferred {len(rows)} rows into '{table}'.")
        except Exception as e:
            pg_conn.rollback()
            print(f"❌ Failed to insert data into '{table}': {e}")
            print("💡 Make sure your Supabase database already has this table schema created!")

    # Close connections cleanly
    sqlite_conn.close()
    pg_conn.close()
    print("\n🎉 Migration process finished!")


if __name__ == "__main__":
    migrate()