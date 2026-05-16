from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict
from database import get_db 

router = APIRouter()

active_games = {}


class GameRoom:
    def __init__(self,room_id:str):
        self.room_id = room_id
        self.board = [["","",""],["","",""],["","",""]]
        self.players: Dict[str, WebSocket] = {}
        self.players_uids = {}
        self.count_of_players = 0
        self.current_turn = "X"
        self.status = "waiting"
        self.win_line = None

    async def connect(self, websocket: WebSocket, uid: str):
        await websocket.accept()
        if uid == self.players_uids["X"]:
            self.count_of_players += 1
            await websocket.send_json({"type":"init","symbol":"X"})
        elif uid == self.players_uids["O"]:
            self.count_of_players += 1
            await websocket.send_json({"type":"init","symbol":"O"})
        else:
            await websocket.send_json({"type":"init","symbol":"SPECTATOR"})
        if self.count_of_players == 2:
            self.status = "playing"
        await self.broadcast_state()

    async def broadcast_state(self):
        payload = {"type":"update","board":self.board,"turn":self.current_turn,"status":self.status,"win_line":self.win_line}
        for ws in self.players.values():
            await ws.send_json(payload)

    async def process_move(self,uid:str,row:int,col:int):
        if not isinstance(row, int) or not isinstance(col, int): return
        if row not in (0,1,2) or col not in (0,1,2): return
        curr_player = None
        for player, player_uid in self.players_uids.items():
            if player_uid == uid: curr_player = player
        if curr_player is None: return
        if self.status != "playing": return
        if curr_player != self.current_turn: return
        if self.board[row][col] != "": return
        self.board[row][col] = curr_player
        win_cells = self.win_checker(curr_player)
        if win_cells:
            self.status = f"win_{curr_player}"
            self.win_line = win_cells
        elif self.draw_checker(curr_player):
            self.status = "draw"
        if self.status.startswith("win_") or self.status == "draw":
            elo_curr = await get_elo_player(self.players_uids[curr_player])
            opp_player = "X" if curr_player == "O" else "O"
            elo_opp = await get_elo_player(self.players_uids[opp_player])
            actual_score = 1.0 if self.status.startswith("win_") else 0.5
            new_elo_curr = calculate_elo(elo_curr,elo_opp,actual_score)
            new_elo_opp = calculate_elo(elo_opp,elo_curr,1-actual_score)
            await update_elo(self.players_uids[curr_player],new_elo_curr,self.players_uids[opp_player],new_elo_opp)
            winner = self.players_uids[curr_player] if self.status.startswith("win_") else None
            result_type = "win" if self.status.startswith("win_") else "draw"
            await record_match(self.players_uids["X"], self.players_uids["O"], winner, result_type)
            await self.broadcast_state()
            await cleanup_room(self.room_id)
            return
        if self.current_turn == "X": self.current_turn = "O"
        else: self.current_turn = "X"
        await self.broadcast_state()

    def win_checker(self,curr_player):
        for r in range(3):
            if self.board[r][0]==curr_player and self.board[r][1]==curr_player and self.board[r][2]==curr_player:
                return [[r,0],[r,1],[r,2]]
        for c in range(3):
            if self.board[0][c]==curr_player and self.board[1][c]==curr_player and self.board[2][c]==curr_player:
                return [[0,c],[1,c],[2,c]]
        if self.board[0][0]==curr_player and self.board[1][1]==curr_player and self.board[2][2]==curr_player:
            return [[0,0],[1,1],[2,2]]
        if self.board[0][2]==curr_player and self.board[1][1]==curr_player and self.board[2][0]==curr_player:
            return [[0,2],[1,1],[2,0]]
        return None

    def draw_checker(self,curr_player):
        for r in range(3):
            for c in range(3):
                if self.board[r][c] == "": return False
        return True

    async def handle_disconnect(self, uid: str):
        disconnected_player = None
        if self.players_uids.get("X") == uid: disconnected_player = "X"
        elif self.players_uids.get("O") == uid: disconnected_player = "O"
        else: disconnected_player = "SPECTATOR"
        if disconnected_player == "SPECTATOR": return
        self.count_of_players = max(0, self.count_of_players - 1)
        if disconnected_player in self.players: del self.players[disconnected_player]
        if self.status.startswith("win_") or self.status == "draw" or self.status.startswith("forfeit_"): return
        if self.status == "waiting":
            await cleanup_room(self.room_id)
            return
        if disconnected_player == "X": self.status = "forfeit_X"
        elif disconnected_player == "O": self.status = "forfeit_O"
        remaining_player = "O" if disconnected_player == "X" else "X"
        elo_remaining = await get_elo_player(self.players_uids[remaining_player])
        elo_disconnected = await get_elo_player(self.players_uids[disconnected_player])
        new_elo_remaining = calculate_elo(elo_remaining,elo_disconnected,1)
        new_elo_disconnected = calculate_elo(elo_disconnected,elo_remaining,0)
        await update_elo(self.players_uids[remaining_player],new_elo_remaining,self.players_uids[disconnected_player],new_elo_disconnected)
        await record_match(self.players_uids["X"], self.players_uids["O"], self.players_uids[remaining_player], "forfeit")
        try:
            payload = {"type":"update","board":self.board,"turn":self.current_turn,"status":self.status,"win_line":self.win_line}
            if remaining_player in self.players:
                await self.players[remaining_player].send_json(payload)
        except: pass
        await cleanup_room(self.room_id)


async def cleanup_room(room_id):
    if room_id in active_games:
        room = active_games[room_id]
        for symbol, ws in list(room.players.items()):
            try: await ws.close()
            except Exception: pass
    from lobby_router import deleteRoom
    await deleteRoom(room_id)
    if room_id in active_games: del active_games[room_id]

async def get_elo_player(uid: str):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT elo_rating from users WHERE uid = %s",(uid,))
    row = cursor.fetchone()
    db.close()
    return row[0] if row else 1200

async def get_room_players(room_id: str):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT player1_uid, player2_uid from room WHERE room_id = %s",(room_id,))
    row = cursor.fetchone()
    db.close()
    return row

async def update_elo(uid1: int, elo1: int, uid2: int, elo2: int):
    db = get_db()
    cursor = db.cursor()
    query = "UPDATE users SET elo_rating = %s WHERE uid = %s"
    cursor.execute(query, (elo1,uid1))
    cursor.execute(query, (elo2,uid2))
    db.commit()
    db.close()

def calculate_elo(rating_player, rating_opponent, actual_score, k_factor=32):
    expected_score = 1 / (1 + 10 ** ((rating_opponent - rating_player) / 400))
    new_rating = rating_player + k_factor * (actual_score - expected_score)
    return round(new_rating)

async def record_match(player1_uid, player2_uid, winner_uid, result_type):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO match_history (player1_uid, player2_uid, winner_uid, result_type) VALUES (%s, %s, %s, %s)",
        (player1_uid, player2_uid, winner_uid, result_type)
    )
    db.commit()
    db.close()


@router.websocket("/ws/game/{room_id}")
async def game_endpoint(websocket: WebSocket, room_id: str):
    uid = websocket.session.get("uid")
    if not uid:
        await websocket.close(code=1008)
        return
    if room_id not in active_games:
        r = await get_room_players(room_id)
        if not r:
            await websocket.close(code=1008)
            return
        active_games[room_id] = GameRoom(room_id)
        active_games[room_id].players_uids["X"] = r[0]
        active_games[room_id].players_uids["O"] = r[1]
    room = active_games[room_id]
    if uid == room.players_uids.get("X"): room.players["X"] = websocket
    elif uid == room.players_uids.get("O"): room.players["O"] = websocket
    else:
        await websocket.close(code=1008)
        return
    await room.connect(websocket, uid)
    try:
        while True:
            data = await websocket.receive_json()
            if data.get("action") == "move" and room.status == "playing":
                row = data.get("row")
                col = data.get("col")
                await room.process_move(uid, row, col)
    except WebSocketDisconnect:
        if room_id in active_games: await room.handle_disconnect(uid)
    except Exception:
        if room_id in active_games: await room.handle_disconnect(uid)
