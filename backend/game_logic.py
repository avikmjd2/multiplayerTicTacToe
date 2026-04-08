from lobby_router import deleteRoom
from fastapi import APIRouter

router = APIRouter()

@router.delete("/delete/room/{id}")
async def deleteR(id:int):
    # print(f"1. Endpoint hit! Requested to delete ID: {id} (Type: {type(id)})")
    await deleteRoom(id)
    return {"status": "request received"}
