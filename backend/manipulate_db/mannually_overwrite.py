import sqlite3
from dotenv import load_dotenv
import os

load_dotenv()

DB_PATH = os.getenv("DB_PATH","./database.db")


def overwrite():  

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    UPDATE users
    SET room_id = -1
    """)
    
    cursor.execute("""
    UPDATE users
    SET is_online = 0
    """)
    
    #include in final
    # cursor.execute("""
    # UPDATE users
    # SET is_online = 0
    # """)

    conn.commit()
    conn.close()

    print("Column updated successfully!")