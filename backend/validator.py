from facial_recognition_module import find_closest_match
from database import get_mongo_db
import numpy as np

def validate(toCheckImg:str):
    client = get_mongo_db()
    mongo_db = client["user"]
    collection = mongo_db["images"]
    allData = {
        user["uid"]: np.array(user["encoding"])
        for user in collection.find(
            {"encoding": {"$exists": True, "$ne": None}},
            {"uid": 1, "encoding": 1, "_id": 0}
    )
}
    
    nearestUID = find_closest_match(toCheckImg,allData)
    
    return(nearestUID)        
