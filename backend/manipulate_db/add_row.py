import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()


try:
    add_col_query = "ALTER TABLE users ADD COLUMN room_id BIGINT DEFAULT -1"
    cursor.execute(add_col_query)
    conn.commit()
    print("Added!!")
except Exception as e:
    print(f"An exception of {e} has occured")
finally:
    conn.close()