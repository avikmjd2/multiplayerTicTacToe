from fastapi import APIRouter
from fastapi.responses import JSONResponse, FileResponse
from database import get_mongo_db,get_db

router = APIRouter()

@router.get("/leaderboard")
def leaderboard_page():
    return FileResponse("../frontend/leaderboard.html")

@router.get("/api/leaderboard")
def get_leaderboard():
    conn = get_db()
    cursor = conn.cursor()
    

    cursor.execute("""
        SELECT uid, name, elo_rating
        FROM users
        ORDER BY elo_rating DESC
    """)

    rows = cursor.fetchall()
    
    result = [
        {"uid": row[0], "name": row[1], "elo_rating": row[2]}
        for row in rows
    ]

    conn.close()
    return JSONResponse(result)