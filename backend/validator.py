from facial_recognition_module import find_closest_match
from database import get_mongo_db

def validate(toCheckImg:str):
    client = get_mongo_db()
    mongo_db = client["user"]
    collection = mongo_db["images"]
    allData = {user["uid"]:user["image"] for user in (collection.find({}, {"uid": 1, "image": 1, "_id": 0}))}
    
    nearestUID = find_closest_match(toCheckImg,allData)
    
    return(nearestUID)        
    
    
