import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()
DB_PATH = os.getenv("DB_PATH", "./arena.db")

connection = sqlite3.connect(DB_PATH)
cursor = connection.cursor()


try:
    add_col_query = "ALTER TABLE users ADD COLUMN room_id INTEGER DEFAULT -1"
    cursor.execute(add_col_query)
    connection.commit()
    print("Added!!")
except Exception as e:
    print(f"An exception of {e} has occured")
finally:
    connection.close()