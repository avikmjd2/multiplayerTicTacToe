from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from starlette.middleware.sessions import SessionMiddleware
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI()


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

@app.get("/register")
def register():
    return FileResponse("../frontend/login.html")


from auth_router import router as auth_router
app.include_router(auth_router)