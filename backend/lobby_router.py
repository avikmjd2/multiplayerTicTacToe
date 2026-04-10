from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
import secrets
from database import get_db
import uuid
import asyncio

router = APIRouter()

class RoomPayload(BaseModel):
    challenge_uid: str
    
class RoomSendPayload(BaseModel):
    room_id: int
    



class Lobby:
    def __init__(self):
        self.active_connections: dict[WebSocket, dict] ={}
        self.uid_to_socket: dict[str, WebSocket] = {} #acts as a map 
        
    async def connect(self,websocket:WebSocket, uid:str, username:str):
        await websocket.accept()
        
        for socketnum, user_data in list(self.active_connections.items()):
            if(user_data["uid"]==uid):
                try:
                    await socketnum.close(code=1008)
                except RuntimeError:
                    pass
                
                del self.active_connections[socketnum]
                
            
        self.active_connections[websocket] = {
            "uid": uid,
            "name": username,
            "is_ready": False,
            "room_id": None
        }
        self.uid_to_socket[uid] = websocket
        await websocket.send_json({"type": "identity", "my_uid": uid})
        await self.broadcast_presence()
        
    async def disconnect(self, websocket: WebSocket):        
        data = self.active_connections.pop(websocket, None)
        if data:
            self.uid_to_socket.pop(data["uid"], None)
            db = get_db()
            db.execute("UPDATE users SET is_online = 0 WHERE uid = ?", (data["uid"],))
            db.commit()
            db.close()
        
        await self.broadcast_presence()
            
    async def broadcast_presence(self):
        # user_list = list(self.active_connections.values())

        user_list = [
                        {"uid": v["uid"], "name": v["name"], "is_ready": v["is_ready"], 
                        "in_game": v["room_id"] is not None}
                        for v in self.active_connections.values()
                    ]
        payload = {
            "type": "presence",
            "count": len(user_list),
            "users": user_list
        }
        
        
        connections = list(self.active_connections.keys())
        
        results = await asyncio.gather(
            *[conn.send_json(payload) for conn in connections], return_exceptions=True
        )
                    
        
        for conn, result in zip(connections, results):
            if isinstance(result, Exception):
                data =self.active_connections.pop(conn, None)
                if data:
                    self.uid_to_socket.pop(data["uid"], None)
                
                
                
            
    async def toggle_ready(self, websocket: WebSocket):
        if websocket in self.active_connections:
            current_status = self.active_connections[websocket]["is_ready"]
            self.active_connections[websocket]["is_ready"] = not current_status
            await self.broadcast_presence()
            
    async def ask_challenge(self, mySocket,opp_uid, my_uid):
        
        opp_socket = self.uid_to_socket.get(opp_uid)
        if(not opp_socket):
            await self.fallBack(mySocket,opp_socket)
            return
        
        
        if(self.active_connections[opp_socket]["room_id"]!=None):
            return
        
        self.active_connections[mySocket]["room_id"] = "awaiting"
        
        self.active_connections[opp_socket]["room_id"] = "awaiting"
        ask_payload = {
            "type":"ask",
            "opp_uid": my_uid,
            "opp_name": self.active_connections[mySocket]["name"]
            
        }
        await opp_socket.send_json(ask_payload)
        await self.broadcast_presence()
        
        asyncio.create_task(self._expire_challenge(mySocket, opp_socket, timeout=30))
        
        
    async def _expire_challenge(self, socket1, socket2, timeout):
        await asyncio.sleep(timeout)
        s1_data = self.active_connections.get(socket1)
        s2_data = self.active_connections.get(socket2)
        if s1_data and s1_data["room_id"] == "awaiting":
            await socket1.send_json({"type": "challenge", "room_id": "timeout"})
            await self.fallBack(socket1, socket2)
        
    async def fallBackById(self,uid1,uid2):
        socket1=None
        socket2 = None 
        socket1 = self.uid_to_socket.get(uid1);
        socket2 = self.uid_to_socket.get(uid2);
        await self.fallBack(socket1,socket2)
        
    async def fallBack(self,mySocket:WebSocket, opp_socket:WebSocket):
        if(mySocket):
            self.active_connections[mySocket]["room_id"] =  None
        if(opp_socket):
            self.active_connections[opp_socket]["room_id"] = None
        await self.broadcast_presence()
        
    async def acceptChallenge(self, mySocket,opp_uid, my_uid, status):
        if(not mySocket): return
        
        opp_socket = self.uid_to_socket.get(opp_uid)
        if not opp_socket:
            await self.fallBack(mySocket, None)
            return
        if(self.active_connections[opp_socket]["room_id"]!= "awaiting" or self.active_connections[mySocket]["room_id"]!= "awaiting"):
            await self.fallBack(mySocket,opp_socket)
            return
        
        if(status=="declined"):
            await opp_socket.send_json({"type":"challenge","room_id":"decline"})
            await self.fallBack(mySocket,opp_socket)
            return
            
        room = await create_room(my_uid=my_uid,opp_uid=opp_uid)
        if(not room):
            await opp_socket.send_json({"type":"challenge","room_id":"error"})
            await mySocket.send_json({"type":"challenge","room_id":"error"})
            # print("I AM HERE1")
            await self.fallBack(mySocket,opp_socket)
        else:
            await mySocket.send_json({"type":"challenge","room_id":room})
            await opp_socket.send_json({"type":"challenge","room_id":room})
            # print("I AM HERE")
            self.active_connections[opp_socket]["room_id"] = room
            self.active_connections[mySocket]["room_id"] = room
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
                
                
            if data.get("action") == "challenge_player":
                await lobby.ask_challenge(websocket,opp_uid=data.get("opp_uid"),my_uid=uid)
                    
            if data.get("action") == "accept_challenge":
                await lobby.acceptChallenge(websocket,opp_uid=data.get("opp_uid"),my_uid=uid,status=data.get("accepted"))

                
                
    except WebSocketDisconnect:
        await lobby.disconnect(websocket=websocket)
        
    except Exception as e:
        print(f"Abrupt disconnect or error: {e}")
        await lobby.disconnect(websocket=websocket)
        

async def create_room(my_uid,opp_uid):

    if(not my_uid or not opp_uid):
        # raise HTTPException(status_code=1008, detail="Not logged in or invalid uid")
        print(f"[DEBUG] create_room failed: my_uid={my_uid}, opp_uid={opp_uid}")
        return None
    
    created = False
    
    room_id = secrets.randbits(50)
    db = get_db()
    cursor = db.cursor()
    
    my_query = cursor.execute("SELECT room_id FROM users WHERE uid = ?",(my_uid,)).fetchone()
    opp_query = cursor.execute("SELECT room_id FROM users WHERE uid = ?",(opp_uid,)).fetchone()
    
    print(f"[DEBUG] create_room: my_query={my_query}, my_query[0]={my_query[0] if my_query else 'None'}, opp_query={opp_query}, opp_query[0]={opp_query[0] if opp_query else 'None'}")
    
    if (my_query and my_query[0] != -1) or (opp_query and opp_query[0] != -1):
        # raise HTTPException(status_code=401, detail="User already playing")
        print(f"[DEBUG] create_room failed: players already in a room")
        return None
    
    try:
        cursor.execute("UPDATE users SET room_id = ? WHERE uid = ?",(room_id,my_uid))
        if cursor.rowcount == 0:
            raise Exception(f"User {my_uid} not found in database")
        cursor.execute("UPDATE users SET room_id = ? WHERE uid = ?",(room_id,opp_uid))
        
        #TODO: Set data in room
        board_id = str(uuid.uuid4())
        cursor.execute("INSERT INTO room (room_id,player1_uid,player2_uid,board_id) VALUES (?,?,?,?)",(room_id,my_uid,opp_uid,board_id))
        if cursor.rowcount == 0:
            raise Exception(f"User {opp_uid} not found in database")
        
        db.commit()
        created = True
    except Exception as e:
        print(f"An error occured whule creating room id. More Details {e}")
        db.rollback()
    finally:
        db.close()
        
        
    if(created):
        return(room_id)
    else:
        return(None)       

    

async def deleteRoom(id:int):
    db = get_db()
    cursor = db.cursor()
    try:
        row = cursor.execute("SELECT player1_uid, player2_uid FROM room WHERE room_id = ?",(id,)).fetchone()         
        if not row:
            return
        uid_1,uid_2 = row
        if(uid_1): 
            cursor.execute("UPDATE users SET room_id = ? WHERE uid = ?",(-1,uid_1))
        if(uid_2):
            cursor.execute("UPDATE users SET room_id = ? WHERE uid = ?",(-1,uid_2))
        cursor.execute("DELETE FROM room WHERE room_id = ?",(id,))
        await lobby.fallBackById(uid_1,uid_2)
        db.commit()
    except Exception as e:
        print(f"An error occured whule deleting room. More Details {e}")
        db.rollback()
    finally:
        db.close()
    
    
    
    