from fastapi import APIRouter
from fastapi.responses import JSONResponse, FileResponse
from database import get_mongo_db

router = APIRouter()

@router.get("/leaderboard")
def leaderboard_page():
    return FileResponse("../frontend/leaderboard.html")

@router.get("/api/leaderboard")
def get_leaderboard():
    client = get_mongo_db()
    db = client["arena"]       # confirm db name with your friend
    users = db["users"]        # confirm collection name with your friend

    rows = list(users.find(
        {},
        {"_id": 0, "uid": 1, "name": 1, "elo_rating": 1}
    ).sort("elo_rating", -1))

    return JSONResponse(rows)