import sqlite3
from dotenv import load_dotenv
import os

load_dotenv()

DB_PATH = os.getenv("DB_PATH","./database.db")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
        uid           TEXT PRIMARY KEY,
        name          TEXT,
        password_hash TEXT,
        elo_rating    INTEGER DEFAULT 1200,
        is_online     INTEGER DEFAULT 0)
""")


conn.commit()
cursor.close()
conn.close()


print("DONE")