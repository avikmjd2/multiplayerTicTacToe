from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from passlib.context import CryptContext
from database import get_db

router = APIRouter(prefix='/auth')
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto",bcrypt__handle="builtin")


class RegisterPayload(BaseModel):
    uid: str
    name: str
    password: str
    
    
class LoginPayload(BaseModel):
    uid:str
    password:str
    
    
@router.post("/register")
def register(payload: RegisterPayload):
    db = get_db()
    cursor = db.cursor()
    existing = cursor.execute(
        "SELECT uid FROM users WHERE uid = ?", (payload.uid,)
    ).fetchone()
    
    if existing:
        db.close()
        raise HTTPException(status_code=400, detail="UID already registered")
    
    
    hashed = pwd_context.hash(payload.password)
    
    cursor.execute(
        "INSERT INTO users (uid, name, password_hash) VALUES (?, ?, ?)",
        (payload.uid, payload.name, hashed)
    )
    
    db.commit()
    db.close()
    
    return {"message": "Registered successfully"}



@router.post("/login")
def login(payload:LoginPayload, request:Request):
    db=get_db()
    cursor = db.cursor()
    
    user = cursor.execute(
        "SELECT * FROM users WHERE uid = ?", (payload.uid,)
    ).fetchone()

    if not user or not pwd_context.verify(payload.password,user["password_hash"]):
        db.close()
        raise HTTPException(status_code=401, detail="Invalid Credintials")
    
    cursor.execute(
        "UPDATE users SET is_online = 1 WHERE uid = ?", (payload.uid,)
    )
    
    db.commit()
    db.close()
    
    
    #save session
    request.session["uid"] = payload.uid
    request.session["name"] = user["name"]
    return {"message": "Login successful", "uid": payload.uid, "name": user["name"]}


@router.post("/logout")
def logout(request: Request):
    uid = request.session.get("uid")
    if uid:
        db = get_db()
        db.execute("UPDATE users SET is_online = 0 WHERE uid = ?", (uid,))
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

