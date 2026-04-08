from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict 

router = APIRouter()

active_games = {}
# This is just a map of random string (room_id) to games

class GameRoom:
    def __init__(self,room_id:str):
        self.room_id = room_id

        self.board = [
            ["","",""],
            ["","",""],
            ["","",""]
        ]

        # {"X" : <Websocket of Player 1> ,..}
        self.players: Dict[str, WebSocket] = {}
        self.current_turn = "X" # X or Y
        self.status = "waiting" # waiting or playing or finished

    async def connect(self, websocket: WebSocket, uid: str):
        await websocket.accept()

        # First person to come is X
        if "X" not in self.players:
            self.players["X"] = websocket
            await websocket.send_json({"type":"init","symbol":"X"})

        # if X is here already (ie second person or more)
        elif "O" not in self.players:
            self.players["O"] = websocket
            self.status = "playing"
            await websocket.send_json({"type":"init","symbol":"O"})

        await self.broadcast_state()

    async def broadcast_state(self):
        # Send whatevers the current board array to both X and O

        payload = {
            "type":"update",
            "board":self.board,
            "turn": self.current_turn,
            "status": self.status
        }
        # self.players has X and O (both Players)
        for ws in self.players.values():
            await ws.send_json(payload)

@router.websocket("/ws/game/{room_id}")
async def game_endpoint(websocket: WebSocket, room_id: str):
    # First doing a security Check to Ensure user loggend in or not

    uid = websocket.session.get("uid")
    if not uid:
        await websocket.close(code=1008)
        return

    # Checking if room exists, if DNE then create

    if room_id not in active_games:
        active_games[room_id] = GameRoom(room_id)

    room = active_games[room_id]

    # Connecting the User
    await room.connect(websocket, uid)

    try:
        # Look for incoming moves infinitely
        while True:
            data = await websocket.receive_json()

            # Handling of the moves comes here

            if data.get("action") == "move" and room.status == "playing":
                row = data.get("row")
                col = data.get("col")
                # await room.process_move(uid, row, col)

    except WebSocketDisconnect:
        # Will do Connection drop handling here 
        # await room.handle_disconnect(uid)


