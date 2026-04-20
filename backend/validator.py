from facial_recognition_module import find_closest_match, build_encodings_cache
from database import get_mongo_db
import numpy as np

cacheBuilt = False
cache = {}

def validate(toCheckImg:str):
    global cacheBuilt, cache
    if not cacheBuilt:
        try:
            print("Building the cache")
            client = get_mongo_db()
            mongo_db = client["user"]
            collection = mongo_db["images"]
            allData = {user["uid"]:user["image"] for user in (collection.find({}, {"uid": 1, "image": 1, "_id": 0}))}
            cache = build_encodings_cache(allData)
            cacheBuilt = True
            print("Cache Built...")
        except Exception as e:
            print(f"Building Cache failed: {e}")
            return(0)
        
    
    
    nearestUID = find_closest_match(toCheckImg,cache)
    
    return(nearestUID)        
