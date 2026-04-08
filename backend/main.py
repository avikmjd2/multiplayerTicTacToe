from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from starlette.middleware.sessions import SessionMiddleware
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
import os

load_dotenv()

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    SessionMiddleware,
    secret_key = os.getenv("SECRET_KEY")
)


app.mount("/static",StaticFiles(directory="../frontend/"),name="static")


@app.get("/")
def root():
    return FileResponse("../frontend/home.html")

@app.get("/home")
def root():
    return FileResponse("../frontend/home.html")

@app.get("/login")
def login():
    return FileResponse("../frontend/login.html")

@app.get("/game/{room_id}")
def game_page(room_id: str):
    return FileResponse("../frontend/game.html")

@app.get("/register")
def register():
    return FileResponse("../frontend/register.html")

@app.get("/lobby")
def lobby():
    return FileResponse("../frontend/lobby.html")


from auth_router import router as auth_router
app.include_router(auth_router)

from game_router import router as game_router_instance
app.include_router(game_router_instance)

from lobby_router import router as lobby_router
app.include_router(lobby_router)

from game_logic import router as game_router
app.include_router(game_router)