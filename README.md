# Identity-Verified Multiplayer Arena

**CS 6.201: Introduction to Software Systems — Course Project**

A full-stack, real-time multiplayer Tic-Tac-Toe web application with biometric (facial recognition) authentication, polyglot database persistence, WebSocket-driven lobby and gameplay, and an Elo-based ranking system.

---

## Table of Contents

1. [Tech Stack](#tech-stack)
2. [Repository Structure](#repository-structure)
3. [Database Schemas](#database-schemas)
4. [Environment Variables](#environment-variables)
5. [Setup & Installation](#setup--installation)
6. [Running the Application](#running-the-application)
7. [Phase-wise Feature Overview](#phase-wise-feature-overview)
8. [Assumptions](#assumptions)
9. [LLM Usage](#llm-usage)

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend Framework | FastAPI (Python 3.13) |
| Relational DB | SQLite |
| Document DB | MongoDB Atlas (via `pymongo`) |
| Real-time Comms | WebSockets (FastAPI native) |
| Facial Recognition | `face-recognition` library (black-box module) |
| Frontend | Vanilla HTML / CSS / JavaScript |
| Package Manager | `uv` |
| Session Management | Starlette `SessionMiddleware` (server-side, cookie-backed) |

---

## Repository Structure

```
project-kernel-panic/
├── backend/
│   ├── main.py                        # FastAPI app entry-point & route mounts
│   ├── database.py                    # SQLite & MongoDB connection helpers
│   ├── init_db.py                     # One-time SQLite schema initialisation
│   ├── scraper.py                     # Phase 1 — batch scraping pipeline
│   ├── facial_recognition_module.py   # Black-box facial recognition (DO NOT MODIFY)
│   ├── validator.py                   # Facial match wrapper (calls find_closest_match)
│   ├── auth_router.py                 # /auth/* — register, login, logout, whoami
│   ├── lobby_router.py                # WebSocket lobby, challenge protocol, room creation
│   ├── game_router.py                 # WebSocket game rooms, Elo calculation
│   ├── game_logic.py                  # Room deletion endpoint
│   ├── leaderboard_router.py          # /leaderboard & /api/leaderboard
│   └── manipulate_db/                 # Dev-time DB helpers
│       ├── add_row.py
│       ├── add_table.py
│       └── mannually_overwrite.py
├── frontend/
│   ├── home.html                      # Landing page
│   ├── login.html                     # Webcam-based facial login
│   ├── register.html                  # New-user registration (face + name)
│   ├── lobby.html                     # Live lobby dashboard
│   ├── game.html                      # Tic-Tac-Toe game board
│   ├── leaderboard.html               # Global Elo leaderboard
│   ├── styles.css                     # Shared stylesheet
│   └── js/
│       ├── login.js
│       ├── register.js
│       ├── lobby.js
│       ├── game.js
│       └── leaderboard.js
├── utils/
│   └── facial_recognition_module.py   # Utility copy of the recognition module
├── batch_data.csv                     # Input roster (uid, name, website_url)
├── pyproject.toml                     # uv project manifest & dependencies
├── uv.lock                           # Locked dependency versions
├── .env                               # Environment configuration (not committed)
└── README.md
```

---

## Database Schemas

### SQLite — Relational Metadata (`database.db`)

#### `users` Table

| Column | Type | Default / Constraint |
|---|---|---|
| `uid` | `TEXT` | **Primary Key** |
| `name` | `TEXT` | — |
| `password_hash` | `TEXT` | — |
| `elo_rating` | `INTEGER` | `1200` |
| `is_online` | `INTEGER` | `0` (treated as boolean) |
| `room_id` | `INTEGER` | `-1` |

```sql
CREATE TABLE IF NOT EXISTS users (
    uid           TEXT PRIMARY KEY,
    name          TEXT,
    password_hash TEXT,
    elo_rating    INTEGER DEFAULT 1200,
    is_online     INTEGER DEFAULT 0,
    room_id       INTEGER DEFAULT -1
);
```

#### `room` Table

| Column | Type | Default / Constraint |
|---|---|---|
| `room_id` | `INTEGER` | **Primary Key** |
| `player1_uid` | `TEXT` | — |
| `player2_uid` | `TEXT` | — |
| `board_id` | `TEXT` | — |

```sql
CREATE TABLE IF NOT EXISTS room (
    room_id       INTEGER PRIMARY KEY,
    player1_uid   TEXT,
    player2_uid   TEXT,
    board_id      TEXT
);
```

### MongoDB Atlas — Binary Asset Storage

- **Database:** `user`
- **Collection:** `images`

Each document in the `images` collection has the following shape:

```json
{
    "uid": "<student-uid>",
    "image": "<Base64-encoded profile image>",
    "encoding": [<128-dimensional face encoding array>]
}
```

The `encoding` field stores the precomputed 128-d face encoding vector (from `face-recognition`) as a list of floats for faster facial matching at login time.

---

## Environment Variables

Create a `.env` file in the project root with the following keys:

```dotenv
SECRET_KEY=<any-random-secret-string>
DB_PATH=<absolute-path-to-database.db>
MONGO_URL=<your-mongodb-atlas-connection-string>
```

| Variable | Purpose |
|---|---|
| `SECRET_KEY` | Used by Starlette `SessionMiddleware` to sign session cookies |
| `DB_PATH` | Absolute path to the SQLite database file |
| `MONGO_URL` | MongoDB Atlas connection URI (SRV format) |

---

## Setup & Installation

### Prerequisites

- **Python 3.13+**
- **[uv](https://docs.astral.sh/uv/)** — Python package manager
- **MongoDB Atlas** cluster (free tier is sufficient)
- **CMake** and **dlib** build dependencies (required by `face-recognition`):

  ```bash
  # Debian / Ubuntu
  sudo apt-get install build-essential cmake libopenblas-dev liblapack-dev libx11-dev
  ```

### 1. Clone the Repository

```bash
git clone <your-github-classroom-repo-url>
cd project-kernel-panic
```

### 2. Install Dependencies

```bash
uv sync
```

This reads `pyproject.toml` and installs all dependencies (including `face-recognition`, `numpy`, `Pillow`, `fastapi`, `uvicorn`, `pymongo`, etc.) into the managed virtual environment.

### 3. Configure Environment

Create the `.env` file in the project root as described in [Environment Variables](#environment-variables).

### 4. Initialise the SQLite Database

```bash
cd backend
uv run python init_db.py
```

This creates `database.db` with the `users` and `room` tables.

### 5. Run the Scraper (Phase 1)

```bash
cd backend
uv run python scraper.py
```

The scraper iterates through `batch_data.csv` and for each student:
- Fetches the profile image from `https://<website_url>/images/pfp.jpg`
- Inserts the student's metadata (`uid`, `name`) into SQLite
- Upserts the Base64 image and its 128-d face encoding into MongoDB

> **Note:** The scraper gracefully handles HTTP 404s, connection timeouts, and missing images — a failure on one student does not crash the pipeline.

---

## Running the Application

### Start the Web Server (FastAPI + WebSocket)

From the **`backend/`** directory:

```bash
cd backend
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The application will be available at **`http://localhost:8000`**.

| URL | Page |
|---|---|
| `/` or `/home` | Landing page |
| `/login` | Facial recognition login |
| `/register` | New user registration |
| `/lobby` | Live multiplayer lobby |
| `/game/<room_id>` | Tic-Tac-Toe game room |
| `/leaderboard` | Global Elo leaderboard |

> **Important:** The WebSocket endpoints for the lobby (`/ws/lobby`) and game rooms (`/ws/game/<room_id>`) are served by the same Uvicorn process — no separate WebSocket server is needed.

---

## Phase-wise Feature Overview

### Phase 1 — The Polyglot Harvester (20 pts)

- **Scraper pipeline** (`scraper.py`) reads `batch_data.csv` and populates both databases simultaneously.
- **SQLite** stores relational user metadata (uid, name, elo_rating, is_online).
- **MongoDB** stores profile images as Base64 strings along with precomputed face encodings.
- **Fault tolerance:** HTTP errors, timeouts, and missing images are caught per-student and logged without halting the pipeline.

### Phase 2 — Biometric Authentication Gateway (20 pts)

- **Webcam capture** on `login.html` uses `navigator.mediaDevices.getUserMedia` to capture a live frame.
- The frame is serialised to Base64 and POST-ed to `/auth/login`.
- The backend fetches all face encodings from MongoDB and calls `find_closest_match()` from the black-box `facial_recognition_module.py`.
- On a successful match (distance ≤ 0.7), the user's `uid` is cross-referenced in SQLite, a server-side session is created, and `is_online` is set to `1`.
- Registration (`/auth/register`) also captures a face image and stores it in MongoDB alongside the user record in SQLite.

### Phase 3 — The Synchronized Arena (35 pts)

- **Live lobby** (`lobby.html` + `lobby_router.py`): displays all online users via WebSocket. The presence grid updates in real-time as users connect or disconnect.
- **Challenge protocol:** User A clicks on User B → a real-time challenge alert appears on B's screen → B accepts or declines.
- **Room isolation:** On mutual acceptance, a dedicated WebSocket room is created. All game traffic is scoped to that room.
- **Server-authoritative Tic-Tac-Toe** (`game_router.py`):
  - The server holds the board state (3×3 array).
  - Clients emit move requests; the server validates turn order and cell availability.
  - After each valid move the updated board is broadcast to both players.
  - **Anti-cheat:** Clients never update the game state directly.

### Phase 4 — Game State Resolution & Elo Reckoning (25 pts)

- **Disconnect handling:** If a player's WebSocket connection drops mid-game, the server awards a forfeit victory to the remaining player and updates Elo ratings accordingly.
- **Elo rating system** (`calculate_elo` in `game_router.py`):

  ```
  E = 1 / (1 + 10^((R_opponent - R_player) / 400))
  R_new = R_old + K × (S - E)     where K = 32
  ```

  Both players' ratings are updated atomically using their pre-match ratings (no cascading updates).
- **Global leaderboard** (`/leaderboard`): fetches all players from SQLite sorted by `elo_rating DESC` and renders a ranked table.

---

## Assumptions

1. **SQLite instead of MySQL.** SQLite is used as the relational database for portability and zero-configuration setup. The schema and SQL syntax are fully compatible with the specification; switching to MySQL would only require changing the connection string and driver.

2. **Face encodings stored in MongoDB.** To speed up the login flow, the 128-dimensional face encoding vector is precomputed during scraping and stored alongside each image document in MongoDB. This avoids re-encoding all images on every login request.

3. **Single-server deployment.** The application is designed to run as a single Uvicorn process serving both HTTP and WebSocket traffic. There is no separate WebSocket server.

4. **Browser webcam access.** The facial login page requires the user to grant camera permissions. The application must be served over `localhost` or HTTPS for `getUserMedia` to work.

5. **`batch_data.csv` is in the project root.** The scraper expects `batch_data.csv` to be located at the project root (one level above `backend/`). If run from the `backend/` directory, it looks for `batch_data.csv` in the current working directory.

6. **MongoDB Atlas free tier.** The MongoDB connection uses a cloud-hosted Atlas cluster (free M0 tier). No local MongoDB installation is required.

7. **`facial_recognition_module.py` is treated as a black box.** Its internal logic has not been modified. The module is called exactly as specified in the project brief via `find_closest_match()` and `get_face_encoding()`.

8. **Session-based authentication.** Server-side sessions (via Starlette `SessionMiddleware`) are used instead of JWTs. The session cookie is signed with `SECRET_KEY`.

9. **Elo K-factor.** A fixed K-factor of 32 is used for all matches as specified in the project requirements.

10. **Room IDs.** Game room IDs are generated as random integers and stored in the `room` table. Each player's current `room_id` is tracked in the `users` table (defaults to `-1` when not in a game).

---

## LLM Usage

> *Insert screenshots of all LLM interactions (prompts and outputs) as a separate PDF here. The screenshots must clearly show the model used (e.g. GitHub Copilot, Gemini, ChatGPT free tier). Paid services such as a Claude subscription are not permitted.*

<!-- Attach llm_usage.pdf to the repository root -->

---

**Team Kernel Panic** · CS 6.201 · April 2026