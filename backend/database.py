import sqlite3
from dotenv import load_dotenv
import os

load_dotenv()


DB_PATH = os.getenv("DB_PATH", "./arena.db")

def get_db():
    try:
        conn = sqlite3.connect(DB_PATH)
        print(DB_PATH)
        conn.row_factory = sqlite3.Row 
        return conn
    except:
        print(DB_PATH)