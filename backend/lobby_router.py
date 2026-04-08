from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
import secrets
from database import get_db
import uuid

router = APIRouter()


class RoomPayload(BaseModel):
    challenge_uid: str
    
class RoomSendPayload(BaseModel):
    room_id: int
    



class Lobby:
    def __init__(self):
        self.active_connections: dict[WebSocket, dict] ={}
        
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
        
        dead_sockets = []
        
        for connection in self.active_connections.keys():
            # if(self.active_connections[connection]["room_id"]==None or self.active_connections[connection]["room_id"]=="awaiting" ):
            if(1):
                try:
                    await connection.send_json(payload)
                except Exception:
                    dead_sockets.append(connection)
                    
        for dead in dead_sockets:
            if dead in self.active_connections:
                del self.active_connections[dead]
            
    async def toggle_ready(self, websocket: WebSocket):
        if websocket in self.active_connections:
            current_status = self.active_connections[websocket]["is_ready"]
            self.active_connections[websocket]["is_ready"] = not current_status
            await self.broadcast_presence()
            
    async def ask_challenge(self, mySocket,opp_uid, my_uid):
        opp_socket = None
        for websocket_paths in self.active_connections.keys():
            if(self.active_connections[websocket_paths]["uid"] == opp_uid):
                opp_socket = websocket_paths
                break
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
        
    async def fallBackById(self,uid1,uid2):
        socket1=None
        socket2 = None
        for sockets, data in self.active_connections.items():
            if(self.active_connections[sockets]["uid"] == uid1):
                socket1 = sockets
            if(self.active_connections[sockets]["uid"] == uid2):
                socket2 = sockets
                
        await self.fallBack(socket1,socket2)
        
    async def fallBack(self,mySocket:WebSocket, opp_socket:WebSocket):
        if(mySocket):
            self.active_connections[mySocket]["room_id"] =  None
        if(opp_socket):
            self.active_connections[opp_socket]["room_id"] = None
        await self.broadcast_presence()
        
    async def acceptChallenge(self, mySocket,opp_uid, my_uid, status):
        if(not mySocket): return
        
        opp_socket = None
        for websocket_paths in self.active_connections.keys():
            if(self.active_connections[websocket_paths]["uid"] == opp_uid):
                opp_socket = websocket_paths
                break
        # print(f"{status} {my_uid} {opp_socket} {mySocket} {opp_uid}")
        if(not opp_socket or self.active_connections[opp_socket]["room_id"]!= "awaiting" or self.active_connections[mySocket]["room_id"]!= "awaiting"):
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
        return None
    
    created = False
    
    room_id = secrets.randbits(63)
    db = get_db()
    cursor = db.cursor()
    
    my_query = cursor.execute("SELECT room_id FROM users WHERE uid = ?",(my_uid,)).fetchone()
    opp_query = cursor.execute("SELECT room_id FROM users WHERE uid = ?",(opp_uid,)).fetchone()
    
    if (my_query and my_query[0] != -1) or (opp_query and opp_query[0] != -1):
        # raise HTTPException(status_code=401, detail="User already playing")
        return None
    
    try:
        cursor.execute("UPDATE users SET room_id = ? WHERE uid = ?",(room_id,my_uid))
        cursor.execute("UPDATE users SET room_id = ? WHERE uid = ?",(room_id,opp_uid))
        
        #TODO: Set data in room
        board_id = str(uuid.uuid4())
        cursor.execute("INSERT INTO room (room_id,player1_uid,player2_uid,board_id) VALUES (?,?,?,?)",(room_id,my_uid,opp_uid,board_id))
        created = True
        
        db.commit()
    except Exception as e:
        print(f"An error occured whule creating room id. More Details {e}")
        db.rollback()
    finally:
        db.close()
        
        
    if(created):
        return(room_id)
    else:
        return(None)       

    

async def deleteRoom(id:str):
    db = get_db()
    cursor = db.cursor()
    try:
        uid_1 = cursor.execute("SELECT player1_uid FROM room WHERE room_id = ?",(id,)).fetchone()
        uid_2 = cursor.execute("SELECT player2_uid FROM room WHERE room_id = ?",(id,)).fetchone()
        if(not(uid_1 and uid_2)):
            return
        uid_1 = uid_1[0]
        uid_2 = uid_2[0]
        cursor.execute("UPDATE users SET room_id = ? WHERE uid = ?",(-1,uid_1))
        cursor.execute("UPDATE users SET room_id = ? WHERE uid = ?",(-1,uid_2))
        cursor.execute("DELETE FROM room WHERE room_id = ?",(id,))
        await lobby.fallBackById(uid_1,uid_2)
        db.commit()
    except Exception as e:
        print(f"An error occured whule deleting room. More Details {e}")
        db.rollback()
    finally:
        db.close()
    
    
    
    
    
    