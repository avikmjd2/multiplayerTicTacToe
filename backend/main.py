from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from starlette.middleware.sessions import SessionMiddleware
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from manipulate_db.mannually_overwrite import overwrite
import os

# Import routers
from leaderboard_router import router as leaderboard_router
from auth_router import router as auth_router
from game_router import router as game_router_instance
from lobby_router import router as lobby_router
from game_logic import router as game_router

load_dotenv()


overwrite()

app = FastAPI()


CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "frontend"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


SECRET_KEY = os.getenv("SECRET_KEY", "fallback_temporary_secret_key_for_production_safetynet")

app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY
)

app.include_router(leaderboard_router)
app.include_router(auth_router)
app.include_router(game_router_instance)
app.include_router(lobby_router)
app.include_router(game_router)


if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")
    print(f"Frontend static directory successfully mounted from: {FRONTEND_DIR}")
else:
    print(f"Warning: Frontend directory could not be located at: {FRONTEND_DIR}")



@app.get("/")
def root():
    return FileResponse(os.path.join(FRONTEND_DIR, "home.html"))

@app.get("/home")
def home(): 
    return FileResponse(os.path.join(FRONTEND_DIR, "home.html"))

@app.get("/login")
def login():
    return FileResponse(os.path.join(FRONTEND_DIR, "login.html"))

@app.get("/game/{room_id}")
def game_page(room_id: str):
    return FileResponse(os.path.join(FRONTEND_DIR, "game.html"))

@app.get("/register")
def register():
    return FileResponse(os.path.join(FRONTEND_DIR, "register.html"))

@app.get("/lobby")
def lobby():
    return FileResponse(os.path.join(FRONTEND_DIR, "lobby.html"))