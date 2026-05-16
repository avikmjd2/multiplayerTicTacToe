import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()



def overwrite():  
    DATABASE_URL = os.getenv("DATABASE_URL")

    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()

    cursor.execute("""
    UPDATE users
    SET room_id = -1
    """)
    
    cursor.execute("""
    UPDATE users
    SET is_online = 0
    """)

    conn.commit()
    conn.close()

    print("Column updated successfully!")