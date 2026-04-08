from lobby_router import deleteRoom
from fastapi import APIRouter

router = APIRouter()

@router.delete("/delete/room/{id}")
def deleteR(id):
    deleteRoom(id)
