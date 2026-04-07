from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from typing import List

router = APIRouter()



class Lobby:
    def __init__(self):
        self.active_connections: dict[WebSocket, dict] ={}
        
    async def connect(self,websocket:WebSocket, uid:str, username:str):
        await websocket.accept()
        
        for socketnum, user_data in list(self.active_connections.items()):
            if(user_data["uid"]==uid):
                await socketnum.close(code=1008)
                del self.active_connections[socketnum]
                
            
        self.active_connections[websocket] = {
            "uid": uid,
            "name": username,
            "is_ready": False 
        }
        await websocket.send_json({"type": "identity", "my_uid": uid})
        await self.broadcast_presence()
        
    async def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            del self.active_connections[websocket]
            await self.broadcast_presence()
            
    async def broadcast_presence(self):
        user_list = list(self.active_connections.values())
        payload = {
            "type": "presence",
            "count": len(user_list),
            "users": user_list
        }
        for connection in self.active_connections.keys():
            await connection.send_json(payload)
            
    async def toggle_ready(self, websocket: WebSocket):
        if websocket in self.active_connections:
            current_status = self.active_connections[websocket]["is_ready"]
            self.active_connections[websocket]["is_ready"] = not current_status
            await self.broadcast_presence()


lobby = Lobby()


@router.websocket("/ws/lobby")
async def lobby_endpoint(websocket:WebSocket):
    # await websocket.accept()
    username = websocket.session.get("name","Unknown")
    uid = websocket.session.get("uid","none")
    if(uid=='none'):
        print("INVALID UID")
        await websocket.close(code=1008)
        return
    await lobby.connect(websocket=websocket,uid=uid,username=username)
    
    try:
        while True:
            # await websocket.receive_text()
            data = await websocket.receive_json()
            if data.get("action") == "toggle_ready":
                await lobby.toggle_ready(websocket)
            if data.get("action") == "non_ready":
                await lobby.toggle_ready(websocket)
                
    except WebSocketDisconnect:
        await lobby.disconnect(websocket=websocket)
    
    