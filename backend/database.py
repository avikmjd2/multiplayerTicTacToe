import os
import psycopg2
from psycopg2.extras import DictCursor
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
MONGO_URL = os.getenv("MONGO_URL")

_mongo_client = None


def get_db():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        conn.cursor_factory = DictCursor
        return conn
    except Exception as e:
        print(f"Failed to connect to PostgreSQL: {e}")
        raise e


def get_mongo_db():
    global _mongo_client
    if _mongo_client is None:
        if not MONGO_URL:
            raise ValueError("MONGO_URL environment variable is missing!")
        _mongo_client = MongoClient(MONGO_URL)
    return _mongo_client