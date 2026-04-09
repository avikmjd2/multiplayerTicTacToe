from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict
from database import get_db 

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
        self.players_uids = {}
        self.count_of_players = 0
        self.current_turn = "X" # X or Y
        self.status = "waiting" # waiting or playing or win_X/O or draw

    async def connect(self, websocket: WebSocket, uid: str):
        await websocket.accept()

        # First person to come is X
        if uid == self.players_uids["X"]:
            self.count_of_players += 1
            await websocket.send_json({"type":"init","symbol":"X"})

        # if X is here already (ie second person or more)
        elif uid == self.players_uids["O"]:
            self.count_of_players += 1
            await websocket.send_json({"type":"init","symbol":"O"})
        else:
            await websocket.send_json({"type":"init","symbol":"SPECTATOR"})

        if self.count_of_players == 2:
            self.status = "playing"

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

    async def process_move(self,uid:str,row:int,col:int):

        # Whose uid is this ie X or Y
        curr_player = None
        for player, player_uid in self.players_uids.items():
            if player_uid == uid:
                curr_player = player
        
        # Validating current player
        if curr_player is None: # neither X nor O (Spectator)
            return
        
        if self.status != "playing": # Game not started or Over
            return

        if curr_player != self.current_turn: # Not curr_player's chance
            return

        # Validiating row and col
        if self.board[row][col] != "": # Cell non empty
            return

        # Update the Board
        self.board[row][col] = curr_player

        # Checking for Win or Draw
        if self.win_checker(curr_player):
            self.status = f"win_{curr_player}" 
        elif self.draw_checker(curr_player):
            self.status = "draw"

        # Inside process_move, after the win/draw check block:
        if self.status.startswith("win_") or self.status == "draw":
            await self.broadcast_state()
            await cleanup_room(self.room_id)
            return


        # Switch turns if neither win nor draw case
        if self.current_turn == "X":
            self.current_turn = "O"
        else:
            self.current_turn = "X"

        await self.broadcast_state()

    def win_checker(self,curr_player):
        # Checking all 3 rows
        for r in range(3):
            if self.board[r][0] == curr_player and self.board[r][1] == curr_player and self.board[r][2] == curr_player:
                return True

        # Checking all 3 cols
        for c in range(3):
            if self.board[0][c] == curr_player and self.board[1][c] == curr_player and self.board[2][c] == curr_player:
                return True

        # Checking Diagonals
        if self.board[0][0] == curr_player and self.board[1][1] == curr_player and self.board[2][2] == curr_player:
            return True
            
        if self.board[0][2] == curr_player and self.board[1][1] == curr_player and self.board[2][0] == curr_player:
            return True
  

    def draw_checker(self,curr_player):
        # if no box left means draw
        for r in range(3):
            for c in range(3):
                if self.board[r][c] == "":
                    return False
        
        return True   

    async def handle_disconnect(self, uid: str):
        player_disconnected = None
        if self.players_uids["X"] == uid:
            player_disconnected = "X"
        elif self.players_uids["O"] == uid:
            player_disconnected = "O"
        else:
            player_disconnected = "SPECTATOR"
        
        if player_disconnected == "X":
            self.status = "forfeit_X"
        elif player_disconnected == "O":
            self.status = "forfeit_O"
        
        remaining_player = "O" if player_disconnected == "X" else "X"
        try:
            payload = {
                "type": "update",
                "board": self.board,
                "turn": self.current_turn,
                "status": self.status
            }

            await self.players[remaining_player].send_json(payload)
        
        except:
            pass

        await cleanup_room(self.room_id)
        

async def cleanup_room(room_id):
    # Person 3's deleteRoom handles:
    # - Setting both players' room_id back to -1 in DB
    # - Deleting the room row from the room table
    # - Calling lobby.fallBackById() so players reappear in lobby
    from lobby_router import deleteRoom
    await deleteRoom(room_id)
    
    # Also remove from our in-memory dictionary
    if room_id in active_games:
        del active_games[room_id]   

async def get_room_players(room_id: str):
    db = get_db()
    cursor = db.cursor()
    row = cursor.execute("SELECT player1_uid, player2_uid from room WHERE room_id = ?",(room_id,)).fetchone()

    db.close()
    return row


@router.websocket("/ws/game/{room_id}")
async def game_endpoint(websocket: WebSocket, room_id: str):
    # First doing a security Check to Ensure user loggend in or not

    uid = websocket.session.get("uid")
    if not uid:
        await websocket.close(code=1008)
        return

    # Checking if room exists, if DNE then create

    if room_id not in active_games:
        r = await get_room_players(room_id)
        if not r:
            await websocket.close(code=1008)
            return
        active_games[room_id] = GameRoom(room_id)

        active_games[room_id].players_uids["X"] = r[0]
        active_games[room_id].players_uids["O"] = r[1]
    
    room = active_games[room_id]

    if uid == room.players_uids.get("X"):
        room.players["X"] = websocket
    elif uid == room.players_uids.get("O"):
        room.players["O"] = websocket 
    else:
        await websocket.close(code=1008)
        return
        
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
                await room.process_move(uid, row, col)

    except WebSocketDisconnect:
        pass
        # Will do Connection drop handling here 
        await room.handle_disconnect(uid)


