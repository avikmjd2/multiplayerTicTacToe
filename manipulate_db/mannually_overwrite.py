import sqlite3
from dotenv import load_dotenv
import os

load_dotenv()

DB_PATH = os.getenv("DB_PATH","./database.db")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("""
UPDATE users
SET room_id = -1
""")

conn.commit()
conn.close()

print("Column updated successfully!")