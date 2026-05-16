import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")


def extract_pg_schema():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
              AND table_type = 'BASE TABLE';
        """)
        tables = cursor.fetchall()

        print("--- Copiable SQL Schema Start ---")
        for (table_name,) in tables:
            cursor.execute("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = %s
                ORDER BY ordinal_position;
            """, (table_name,))
            columns = cursor.fetchall()

            print(f"CREATE TABLE {table_name} (")
            col_defs = []
            for col_name, data_type, nullable, default in columns:
                line = f"    {col_name} {data_type}"
                if default:
                    line += f" DEFAULT {default}"
                if nullable == "NO":
                    line += " NOT NULL"
                col_defs.append(line)
            print(",\n".join(col_defs))
            print(");\n")
        print("--- Copiable SQL Schema End ---")

        conn.close()

    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    extract_pg_schema()