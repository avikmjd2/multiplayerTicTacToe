# CS6.201 Arena Project — Teammate Handoff Doc
## Your Scope: Game Logic, Elo, Leaderboard

> **Written by:** Avik (Person 2)  
> **For:** Person 3  
> **Stack:** FastAPI + SQLite + WebSockets (Python backend, vanilla HTML/JS frontend)

---

## 1. What Avik Already Built (What You're Plugging Into)

Before you write a single line, understand the system state you're receiving.

### 1.1 Database (SQLite via `init_db.py`)

Two tables:

**`users`**
| Column | Type | Default |
|---|---|---|
| `uid` | TEXT (UUID) | Primary Key |
| `name` | TEXT | — |
| `password_hash` | TEXT | — |
| `elo_rating` | INTEGER | 1200 |
| `is_online` | INTEGER | 0 (false) |
| `room_id` | INTEGER | -1 (no room) |

**`room`**
| Column | Type | Notes |
|---|---|---|
| `room_id` | INTEGER | Primary Key (random 50-bit int) |
| `player1_uid` | TEXT | UID of challenger acceptor |
| `player2_uid` | TEXT | UID of original challenger |
| `board_id` | TEXT (UUID) | Unique ID for this game's board state |

### 1.2 Auth & Session

- Login is **facial recognition only** (no passwords at login time)
- On successful login, a **server-side session** is set:
  ```
  request.session["uid"]  = "<uuid>"
  request.session["name"] = "<display name>"
  ```
- `is_online` is set to `1` on login, `0` on logout
- WebSockets can read the session via `websocket.session.get("uid")`

### 1.3 The Lobby Flow (What Avik Handles End-to-End)

```
User A opens /lobby  →  WS connects to /ws/lobby
User A clicks User B →  WS message: { action: "challenge_player", opp_uid: "..." }
User B receives popup → WS message: { type: "ask", opp_uid: "...", opp_name: "..." }
User B accepts        →  WS message: { action: "accept_challenge", opp_uid: "...", accepted: "accepted" }
Server calls create_room() → inserts into `room` table, updates both users' room_id
Both clients receive  → WS message: { type: "challenge", room_id: <number> }
```

**At this point, Avik's job ends. Your job begins.**

The moment both clients receive `{ type: "challenge", room_id: <number> }`, the frontend redirects them to the game page (e.g., `/game?room_id=<number>`). You own everything from here.

---

## 2. Your Deliverables

| # | What | Where |
|---|---|---|
| 1 | Game WebSocket endpoint | `POST /ws/game/{room_id}` |
| 2 | Server-side Tic-Tac-Toe state + validation | Inside your WS handler |
| 3 | Win/draw detection + broadcast | Same handler |
| 4 | Disconnect → forfeit logic | WebSocketDisconnect handler |
| 5 | Elo calculation + MySQL update | Helper function |
| 6 | Leaderboard page | `GET /leaderboard` → HTML |
| 7 | Game board frontend | `/game` page + JS |

---

## 3. How to Set Up Your Router

Create a file `game_router.py`. Register it in `main.py`:

```python
# In main.py (add at bottom)
from game_router import router as game_router_ws
app.include_router(game_router_ws)

# Also add the leaderboard page route:
@app.get("/game")
def game_page():
    return FileResponse("../frontend/game.html")

@app.get("/leaderboard")
def leaderboard_page():
    return FileResponse("../frontend/leaderboard.html")
```

Note: `game_logic.py` already exists and has a `/delete/room/{id}` endpoint. That's a helper Avik uses internally. **Don't touch it.** Your router is separate.

---

## 4. Database Access

Use the existing `get_db()` from `database.py`:

```python
from database import get_db

db = get_db()
cursor = db.cursor()
# ... do your queries ...
db.commit()
db.close()
```

`get_db()` returns a `sqlite3.Connection` with `row_factory = sqlite3.Row`, so rows behave like dicts:
```python
row = cursor.execute("SELECT * FROM room WHERE room_id = ?", (room_id,)).fetchone()
row["player1_uid"]  # works
row["player2_uid"]  # works
```

---

## 5. Game WebSocket: Architecture

### 5.1 Endpoint Signature

```python
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from database import get_db
import asyncio

router = APIRouter()

@router.websocket("/ws/game/{room_id}")
async def game_endpoint(websocket: WebSocket, room_id: int):
    uid = websocket.session.get("uid")
    if not uid:
        await websocket.close(code=1008)
        return
    # ... rest of logic
```

### 5.2 State You Need to Track (in-memory, per room)

```python
# Global dict — maps room_id to game state
active_games: dict[int, dict] = {}

# Structure of each game entry:
{
    "board": [None]*9,           # 9-cell flat array. None = empty, "X" or "O"
    "players": {},               # { uid: "X" or "O" }
    "turn": None,                # uid of whose turn it is
    "sockets": {},               # { uid: WebSocket }
    "over": False
}
```

### 5.3 On Connection

When a player connects to `/ws/game/{room_id}`:

1. Accept the WebSocket
2. Look up the `room` table to get `player1_uid` and `player2_uid`
3. Verify the connecting `uid` is one of those two — close with 1008 if not
4. Assign symbols: `player1_uid → "X"`, `player2_uid → "O"`
5. Set `turn` to `player1_uid` when **both** players are connected
6. Broadcast game start to both:

```json
{ "type": "game_start", "your_symbol": "X", "board": [null,null,...], "turn": "<uid>" }
```

### 5.4 On Move

Client sends:
```json
{ "action": "move", "cell": 4 }
```

Server must validate (in this exact order):
1. Is `game["over"]` false?
2. Is it this player's turn? (`game["turn"] == uid`)
3. Is `game["board"][cell]` currently `None`?

If all pass:
- Update `game["board"][cell]` = player's symbol
- Check win/draw (see Section 6)
- If game continues: flip turn
- Broadcast to **both** clients:

```json
{
  "type": "board_update",
  "board": [...],
  "turn": "<uid of next player>",
  "last_move": { "cell": 4, "symbol": "X", "by": "<uid>" }
}
```

If game ends (see Section 6), broadcast result and call your Elo update function.

---

## 6. Win / Draw Detection

```python
WIN_PATTERNS = [
    [0,1,2],[3,4,5],[6,7,8],  # rows
    [0,3,6],[1,4,7],[2,5,8],  # cols
    [0,4,8],[2,4,6]           # diags
]

def check_winner(board):
    for a, b, c in WIN_PATTERNS:
        if board[a] and board[a] == board[b] == board[c]:
            return board[a]  # returns "X" or "O"
    if all(cell is not None for cell in board):
        return "draw"
    return None  # game continues
```

Broadcast on game end:
```json
{
  "type": "game_over",
  "result": "win",          // "win", "draw", or "forfeit"
  "winner_uid": "<uid>",    // null on draw
  "board": [...]
}
```

---

## 7. Disconnect / Forfeit

```python
except WebSocketDisconnect:
    game = active_games.get(room_id)
    if game and not game["over"]:
        game["over"] = True
        # The player who disconnected loses
        loser_uid = uid
        winner_uid = [u for u in game["players"] if u != loser_uid][0]
        
        # Notify the remaining player
        winner_socket = game["sockets"].get(winner_uid)
        if winner_socket:
            await winner_socket.send_json({
                "type": "game_over",
                "result": "forfeit",
                "winner_uid": winner_uid
            })
        
        # Update Elo
        await update_elo(winner_uid, loser_uid, result="win")
        
    # Clean up
    await cleanup_room(room_id)
```

---

## 8. Elo Calculation

Use the exact formula from the project spec:

```python
def calculate_elo(r_player, r_opponent, score):
    """
    score: 1.0 = win, 0.5 = draw, 0.0 = loss
    Returns new rating for the player.
    """
    K = 32
    E = 1 / (1 + 10 ** ((r_opponent - r_player) / 400))
    return round(r_player + K * (score - E))


async def update_elo(winner_uid, loser_uid, result="win"):
    """result: 'win' or 'draw'"""
    db = get_db()
    cursor = db.cursor()
    
    r1 = cursor.execute("SELECT elo_rating FROM users WHERE uid = ?", (winner_uid,)).fetchone()["elo_rating"]
    r2 = cursor.execute("SELECT elo_rating FROM users WHERE uid = ?", (loser_uid,)).fetchone()["elo_rating"]
    
    if result == "draw":
        new_r1 = calculate_elo(r1, r2, 0.5)
        new_r2 = calculate_elo(r2, r1, 0.5)
    else:  # win/loss or forfeit
        new_r1 = calculate_elo(r1, r2, 1.0)  # winner
        new_r2 = calculate_elo(r2, r1, 0.0)  # loser
    
    # IMPORTANT: Use r1/r2 (pre-match ratings) for BOTH calculations.
    # Do NOT use new_r1 when computing new_r2.
    
    cursor.execute("UPDATE users SET elo_rating = ? WHERE uid = ?", (new_r1, winner_uid))
    cursor.execute("UPDATE users SET elo_rating = ? WHERE uid = ?", (new_r2, loser_uid))
    db.commit()
    db.close()
```

---

## 9. Room Cleanup After Game

After every game ends (win, draw, or forfeit), clean up the room:

```python
async def cleanup_room(room_id: int):
    # Call Avik's existing delete endpoint logic
    # Import directly from lobby_router
    from lobby_router import deleteRoom
    await deleteRoom(room_id)
    
    # Remove from in-memory state
    if room_id in active_games:
        del active_games[room_id]
```

`deleteRoom(id)` in `lobby_router.py` already handles:
- Setting both players' `room_id` back to `-1` in the DB
- Deleting the row from the `room` table
- Calling `lobby.fallBackById()` so the players reappear in the lobby

---

## 10. Leaderboard Endpoint

```python
# In main.py or a separate leaderboard_router.py
from fastapi.responses import JSONResponse

@app.get("/api/leaderboard")
def get_leaderboard():
    db = get_db()
    cursor = db.cursor()
    rows = cursor.execute(
        "SELECT uid, name, elo_rating FROM users ORDER BY elo_rating DESC"
    ).fetchall()
    db.close()
    return JSONResponse([dict(r) for r in rows])
```

Your leaderboard HTML page just fetches `/api/leaderboard` and renders a table.

---

## 11. Frontend: What the Client Sends / Receives

### Game Page JS Flow

```javascript
// 1. Get room_id from URL
const params = new URLSearchParams(window.location.search);
const roomId = params.get("room_id");

// 2. Connect to game WS
const ws = new WebSocket(`ws://${location.host}/ws/game/${roomId}`);

// 3. Handle messages
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    
    if (data.type === "game_start") {
        mySymbol = data.your_symbol;
        renderBoard(data.board);
        updateTurnIndicator(data.turn);
    }
    
    if (data.type === "board_update") {
        renderBoard(data.board);
        updateTurnIndicator(data.turn);
    }
    
    if (data.type === "game_over") {
        showResult(data);
        // Optionally redirect back to lobby after a delay
    }
};

// 4. Send a move
function clickCell(index) {
    ws.send(JSON.stringify({ action: "move", cell: index }));
}
```

### Lobby → Game Redirect (Already in Avik's lobby.js)

In `lobby.js`, when the client receives `{ type: "challenge", room_id: <number> }`, it does:

```javascript
window.location.href = `/game?room_id=${data.room_id}`;
```

So the game page will always have `room_id` in the query string.

---

## 12. Complete Message Protocol Reference

### Server → Client

| `type` | When | Key Fields |
|---|---|---|
| `game_start` | Both players connected | `your_symbol`, `board`, `turn` |
| `board_update` | After valid move | `board`, `turn`, `last_move` |
| `game_over` | Win / draw / forfeit | `result`, `winner_uid`, `board` |
| `error` | Invalid move attempt | `message` |

### Client → Server

| `action` | When | Key Fields |
|---|---|---|
| `move` | Player clicks a cell | `cell` (0–8) |

---

## 13. Checklist Before Viva

- [ ] `/ws/game/{room_id}` rejects unauthorized connections (not in that room)
- [ ] Board state is server-side only — clients never set board state directly
- [ ] Turn enforcement: server ignores moves from the wrong player
- [ ] Win, draw, and forfeit all trigger Elo update
- [ ] Elo uses pre-match ratings for both calculations (not sequential)
- [ ] `deleteRoom()` is called after every game conclusion
- [ ] Leaderboard sorts by `elo_rating DESC` and shows all users
- [ ] At least one commit by 10 April (40% milestone check)

---

## 14. Files You Will Create

```
backend/
  game_router.py       ← your main file

frontend/
  game.html            ← game board UI
  leaderboard.html     ← leaderboard table
  js/
    game.js            ← game WS client
    leaderboard.js     ← fetch + render leaderboard
```

Do **not** modify: `main.py` (except to include your router), `lobby_router.py`, `game_logic.py`, `auth_router.py`, `database.py`, `facial_recognition_module.py`.
