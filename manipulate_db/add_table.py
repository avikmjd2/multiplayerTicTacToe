import sqlite3
from dotenv import load_dotenv
import os

load_dotenv()

DB_PATH = os.getenv("DB_PATH","./database.db")
conn = sqlite3.connect(DB_PATH)


cursor = conn.cursor()


cursor.execute("""
    CREATE TABLE IF NOT EXISTS room (
    room_id       INTEGER PRIMARY KEY,
    player1_uid   TEXT,
    player2_uid   TEXT,
    board_id      TEXT      
    )
""")


conn.commit()


conn.close()

print("Table created successfully!")