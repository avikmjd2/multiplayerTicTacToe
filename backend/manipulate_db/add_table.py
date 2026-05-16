import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
conn = psycopg2.connect(DATABASE_URL)


cursor = conn.cursor()


cursor.execute("""
    CREATE TABLE IF NOT EXISTS room (
    room_id       BIGINT PRIMARY KEY,
    player1_uid   TEXT,
    player2_uid   TEXT,
    board_id      TEXT      
    )
""")


conn.commit()


conn.close()

print("Table created successfully!")