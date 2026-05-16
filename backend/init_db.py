import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()

cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
        uid           TEXT PRIMARY KEY,
        name          TEXT,
        password_hash TEXT,
        elo_rating    INTEGER DEFAULT 1200,
        is_online     INTEGER DEFAULT 0,
        room_id       BIGINT DEFAULT -1           
        )
""")

cursor.execute("""
        CREATE TABLE IF NOT EXISTS room (
        room_id       BIGINT PRIMARY KEY,
        player1_uid   TEXT,
        player2_uid   TEXT,
        board_id      TEXT      
        )
""")

cursor.execute("""
        CREATE TABLE IF NOT EXISTS match_history (
        match_id      SERIAL PRIMARY KEY,
        player1_uid   TEXT,
        player2_uid   TEXT,
        winner_uid    TEXT,   
        result_type   TEXT, 
        timestamp     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
""")

cursor.execute("CREATE INDEX IF NOT EXISTS idx_player1 ON match_history(player1_uid)")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_player2 ON match_history(player2_uid)")



conn.commit()
cursor.close()
conn.close()


print("DONE")