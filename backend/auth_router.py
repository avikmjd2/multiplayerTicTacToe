from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from passlib.context import CryptContext
from database import get_db,get_mongo_db
from bson import ObjectId
from validator import validate
from facial_recognition_module import get_face_encoding
import uuid

router = APIRouter(prefix='/auth')
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto",bcrypt__handle="builtin")

class PyObjectId(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return str(v)
    

class RegisterPayload(BaseModel):
    name: str
    password: str
    image: str
    
    
class LoginPayload(BaseModel):
    image:str
    
    
class newItem(BaseModel):
    uid:str
    image:str
    
    
@router.post("/register")
def register(payload: RegisterPayload):
    db = get_db()
    cursor = db.cursor()
    
    existing = validate(payload.image)
    if existing:
        db.close()
        raise HTTPException(status_code=400, detail="IMAGE already registered")
    
    
    hashed = pwd_context.hash(payload.password)
    user_uuid = str(uuid.uuid4())

    try:
        cursor.execute(
            "INSERT INTO users (uid, name, password_hash) VALUES (%s, %s, %s)",
            (user_uuid, payload.name, hashed)
        )
        
        db.commit()
        
    except Exception as e:
        db.close()
        raise HTTPException(status_code=500, detail=f"Failed to save user info: {e}")
    
    img_encoding = get_face_encoding(payload.image)
    
    try:
        client = get_mongo_db()
        if not client:
            raise HTTPException(status_code=500, detail="Could not connect to MongoDB")
        
        mongo_db = client["user"]
        collection = mongo_db["images"]
        
        collection.insert_one({
            "uid": user_uuid,
            "image": payload.image,
            "encoding": img_encoding if img_encoding is not None else None
        })
    except HTTPException:
        cursor.execute("DELETE FROM users WHERE uid = %s",(user_uuid,))
        db.commit()
        db.close()
        raise
    except Exception:
        db.rollback()
        cursor.execute("DELETE FROM users WHERE uid = %s",(user_uuid,))
        db.commit()
        db.close()
        raise HTTPException(status_code=500, detail="Image save failed. Registration reverted.")
    
    db.close()
    return {"message": "Registered successfully"}



@router.post("/login")
def login(payload:LoginPayload, request:Request):
    
    existing = validate(payload.image)
    if not existing:
        raise HTTPException(status_code=401, detail="Invalid FACE")
    db=get_db()
    cursor = db.cursor()
    
    cursor.execute(
        "SELECT * FROM users WHERE uid = %s", (existing,)
    )
    user = cursor.fetchone()

    if not user:
        db.close()
        raise HTTPException(status_code=401, detail="Invalid User")
    
    cursor.execute(
        "UPDATE users SET is_online = 1 WHERE uid = %s", (existing,)
    )
    
    db.commit()
    db.close()
    
    
    request.session["uid"] = existing
    request.session["name"] = user["name"]
    return {"message": "Login successful", "uid": existing, "name": user["name"]}


@router.post("/logout")
def logout(request: Request):
    uid = request.session.get("uid")
    if uid:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("UPDATE users SET is_online = 0 WHERE uid = %s", (uid,))
        db.commit()
        db.close()
        
    request.session.clear()
    return {"message": "Logged out"}


@router.get("/whoami")
def whoami(request:Request):
    uid = request.session.get("uid")
    if not uid:
        raise HTTPException(status_code=401, detail="Not logged in")
    
    return {"uid": uid, "name": request.session.get("name")}



async def get_recent_matches(uid: str):
    db = get_db()
    cursor = db.cursor()
    
    query = """
        SELECT 
            player1_uid, 
            player2_uid, 
            winner_uid, 
            result_type, 
            timestamp,
            COUNT(*) OVER() as total_count
        FROM match_history 
        WHERE player1_uid = %s OR player2_uid = %s
        ORDER BY timestamp DESC
        LIMIT 10
    """
    
    cursor.execute(query, (uid, uid))
    rows = cursor.fetchall()
    db.close()

    if not rows:
        return {"total_played": 0, "recent_matches": []}

    total_played = rows[0]["total_count"]
    
    match_data = []
    for row in rows:
        p1 = row["player1_uid"]
        p2 = row["player2_uid"]
        winner = row["winner_uid"]
        res_type = row["result_type"]
        timestamp = row["timestamp"]
        
        
        opponent_uid = p2 if p1 == uid else p1
        
        if res_type == "draw":
            outcome = "Draw"
        elif winner == uid:
            outcome = "Win"
        else:
            outcome = "Loss"
            
        match_data.append({
            "opponent_uid": opponent_uid,
            "outcome": outcome,
            "result_type": res_type, 
            "timestamp": str(timestamp)
        })

    return {
        "total_played": total_played,
        "recent_matches": match_data
    }




@router.get("/compdata")
async def getInfo(request:Request):
        
    uid = request.session.get("uid")
    if not uid:
        raise HTTPException(status_code=401, detail="Not logged in")
    
    db=get_db()
    cursor = db.cursor()
    
    cursor.execute(
        "SELECT * FROM users WHERE uid = %s", (uid,)
    )
    user = cursor.fetchone()
    
    if not user:
        db.close()
        raise HTTPException(status_code=401, detail="Invalid User")
    
    elo_rate = user["elo_rating"]
    if not elo_rate:
        elo_rate = "error"
    
    match_result = await get_recent_matches(uid)
    
    for match in match_result["recent_matches"]:
        cursor.execute(
            "SELECT name FROM users WHERE uid = %s", (match["opponent_uid"],)
        )
        opp = cursor.fetchone()
        match["opponent_name"] = opp["name"] if opp else "Unknown"
    
    db.close()
    
    return {
        "uid": uid, 
        "name": request.session.get("name"),
        "elo": elo_rate,
        "total_played": match_result["total_played"],
        "recent_matches": match_result["recent_matches"]
    }

