import sqlite3
from dotenv import load_dotenv
import os
from pymongo import MongoClient

load_dotenv()


DB_PATH = os.getenv("DB_PATH", "./arena.db")
MONGO_URL = os.getenv("MONGO_URL")

_mongo_client = None


def get_db():
    try:
        conn = sqlite3.connect(DB_PATH)
        # print(DB_PATH)
        conn.row_factory = sqlite3.Row 
        return conn
    except:
        print(DB_PATH)
        
        
def get_mongo_db():
    global _mongo_client
    if _mongo_client is None:
        _mongo_client = MongoClient(MONGO_URL)
    return _mongo_client
    # client = MongoClient(MONGO_URL)
    # try:
    #     client.admin.command('ping')
    #     return(client)
    # except Exception as e:
    #     print(e)
    #     return None
        
        